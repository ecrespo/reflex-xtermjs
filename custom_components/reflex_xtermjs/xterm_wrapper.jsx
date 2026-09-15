/**
 * reflex-xtermjs - React wrapper around xterm.js for Reflex.
 *
 * The wrapper owns the whole terminal lifecycle:
 *   - creates a single Terminal instance per mount,
 *   - loads the addons requested through the `addons` prop,
 *   - keeps terminal options in sync with React props without re-creating
 *     the terminal,
 *   - optionally attaches the terminal to a WebSocket (PTY backend),
 *   - publishes an imperative API on `window.__reflexXterm` so the Reflex
 *     backend can drive the terminal through `rx.call_script`.
 *
 * Everything that touches `document` happens inside `useEffect`, and the
 * Python side wraps this component as a `NoSSRComponent`, so the module is
 * never evaluated during server-side rendering.
 */
import React, { useCallback, useEffect, useLayoutEffect, useRef } from "react";

import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { SearchAddon } from "@xterm/addon-search";
import { WebLinksAddon } from "@xterm/addon-web-links";
import { SerializeAddon } from "@xterm/addon-serialize";
import { AttachAddon } from "@xterm/addon-attach";
import { ClipboardAddon } from "@xterm/addon-clipboard";
import { WebglAddon } from "@xterm/addon-webgl";
import { Unicode11Addon } from "@xterm/addon-unicode11";
import { UnicodeGraphemesAddon } from "@xterm/addon-unicode-graphemes";
import { ImageAddon } from "@xterm/addon-image";
import { LigaturesAddon } from "@xterm/addon-ligatures";
import { ProgressAddon } from "@xterm/addon-progress";

import "@xterm/xterm/css/xterm.css";

/**
 * `@xterm/addon-canvas` still declares a peer dependency on xterm 5.x, so it is
 * deliberately NOT a static import: pulling it in would break dependency
 * resolution for every user of this component. It is loaded lazily, through an
 * indirect specifier so the bundler leaves it alone, and only when the app
 * actually asks for the canvas renderer AND the package is installed.
 */
const CANVAS_ADDON_PACKAGE = "@xterm/addon-canvas";

/**
 * Addons that call into xterm.js' proposed (unstable) API. Loading any of them
 * throws unless `allowProposedApi` is on, so the wrapper turns the option on by
 * itself when one is requested and the app has not decided for itself.
 */
const PROPOSED_API_ADDONS = new Set([
  "unicode11",
  "unicode-graphemes",
  "ligatures",
  "image",
  "progress",
  "serialize",
]);

/** Terminal options forwarded verbatim to xterm.js when defined. */
const TERMINAL_OPTION_KEYS = [
  "allowProposedApi",
  "allowTransparency",
  "altClickMovesCursor",
  "convertEol",
  "cursorBlink",
  "cursorInactiveStyle",
  "cursorStyle",
  "cursorWidth",
  "customGlyphs",
  "disableStdin",
  "drawBoldTextInBrightColors",
  "fastScrollModifier",
  "fastScrollSensitivity",
  "fontFamily",
  "fontSize",
  "fontWeight",
  "fontWeightBold",
  "ignoreBracketedPasteMode",
  "letterSpacing",
  "lineHeight",
  "logLevel",
  "macOptionClickForcesSelection",
  "macOptionIsMeta",
  "minimumContrastRatio",
  "overviewRuler",
  "reflowCursorLine",
  "rescaleOverlappingGlyphs",
  "rightClickSelectsWord",
  "screenReaderMode",
  "scrollOnEraseInDisplay",
  "scrollOnUserInput",
  "scrollSensitivity",
  "scrollback",
  "smoothScrollDuration",
  "tabStopWidth",
  "theme",
  "windowOptions",
  "windowsPty",
  "wordSeparator",
];

/** Build an xterm options object out of the defined props only. */
function collectOptions(props, requestedAddons) {
  const options = {};
  for (const key of TERMINAL_OPTION_KEYS) {
    if (props[key] !== undefined && props[key] !== null) {
      options[key] = props[key];
    }
  }
  if (options.allowProposedApi === undefined) {
    const needsProposedApi = (requestedAddons || []).some((name) =>
      PROPOSED_API_ADDONS.has(name),
    );
    if (needsProposedApi) {
      options.allowProposedApi = true;
    }
  }
  return options;
}

/** Call a Reflex event handler if the app supplied one. */
function fire(handlerRef, name, ...args) {
  const handler = handlerRef.current?.[name];
  if (typeof handler === "function") {
    try {
      handler(...args);
    } catch (error) {
      console.error(`[reflex-xtermjs] handler ${name} failed`, error);
    }
  }
}

/** Serialize a KeyboardEvent down to something the backend can receive. */
function describeKeyEvent(domEvent) {
  if (!domEvent) {
    return {};
  }
  return {
    key: domEvent.key,
    code: domEvent.code,
    keyCode: domEvent.keyCode,
    ctrlKey: !!domEvent.ctrlKey,
    altKey: !!domEvent.altKey,
    shiftKey: !!domEvent.shiftKey,
    metaKey: !!domEvent.metaKey,
    type: domEvent.type,
  };
}

/** The global registry the Python helpers in `api.py` talk to. */
function registry() {
  if (typeof window === "undefined") {
    return {};
  }
  if (!window.__reflexXterm) {
    window.__reflexXterm = {};
  }
  return window.__reflexXterm;
}

export function XTerm(props) {
  const {
    terminalId = "default",
    cols,
    rows,
    addons = ["fit", "web-links"],
    renderer = "dom",
    autoFit = true,
    fitDebounceMs = 60,
    initialText,
    websocketUrl,
    attachBidirectional = true,
    reconnect = false,
    reconnectDelayMs = 2000,
    sendResizeOnSocket = true,
    searchOptions,
    imageOptions,
    ligatureOptions,
    unicodeVersion,
    readOnly = false,
    className,
    style,
    ...rest
  } = props;

  const containerRef = useRef(null);
  const termRef = useRef(null);
  const addonsRef = useRef({});
  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const disposablesRef = useRef([]);
  const mountedRef = useRef(false);

  /* Handlers live in a ref so xterm listeners never capture a stale closure. */
  const handlersRef = useRef({});
  handlersRef.current = {
    onData: props.onData,
    onKey: props.onKey,
    onBinary: props.onBinary,
    onTitleChange: props.onTitleChange,
    onResize: props.onResize,
    onBell: props.onBell,
    onLineFeed: props.onLineFeed,
    onCursorMove: props.onCursorMove,
    onScroll: props.onScroll,
    onSelectionChange: props.onSelectionChange,
    onRender: props.onRender,
    onWriteParsed: props.onWriteParsed,
    onReady: props.onReady,
    onSearchResults: props.onSearchResults,
    onProgress: props.onProgress,
    onContextLoss: props.onContextLoss,
    onLinkClick: props.onLinkClick,
    onSocketOpen: props.onSocketOpen,
    onSocketClose: props.onSocketClose,
    onSocketError: props.onSocketError,
  };

  /* Latest socket-related settings, read by the connect routine. */
  const socketConfigRef = useRef({});
  socketConfigRef.current = {
    attachBidirectional,
    reconnect,
    reconnectDelayMs,
    sendResizeOnSocket,
  };

  /* ------------------------------------------------------------------ */
  /* WebSocket / PTY plumbing                                            */
  /* ------------------------------------------------------------------ */

  const sendResize = useCallback(() => {
    const socket = socketRef.current;
    const term = termRef.current;
    if (!term || !socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }
    if (!socketConfigRef.current.sendResizeOnSocket) {
      return;
    }
    /* Out-of-band control frame; the reference PTY backend understands it. */
    try {
      socket.send(
        JSON.stringify({ type: "resize", cols: term.cols, rows: term.rows }),
      );
    } catch (error) {
      console.warn("[reflex-xtermjs] could not send resize", error);
    }
  }, []);

  const closeSocket = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    const attach = addonsRef.current.attach;
    if (attach) {
      try {
        attach.dispose();
      } catch (_) {
        /* already disposed */
      }
      delete addonsRef.current.attach;
    }
    const socket = socketRef.current;
    socketRef.current = null;
    if (socket && socket.readyState <= WebSocket.OPEN) {
      socket.close();
    }
  }, []);

  const openSocket = useCallback(
    (url) => {
      const term = termRef.current;
      if (!term || !url) {
        return;
      }
      closeSocket();

      let resolved = url;
      if (typeof window !== "undefined" && !/^wss?:\/\//i.test(url)) {
        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        resolved = `${proto}//${window.location.host}${
          url.startsWith("/") ? "" : "/"
        }${url}`;
      }

      let socket;
      try {
        socket = new WebSocket(resolved);
        /* AttachAddon writes Uint8Array directly; Blobs would not work. */
        socket.binaryType = "arraybuffer";
      } catch (error) {
        fire(handlersRef, "onSocketError", String(error));
        return;
      }
      socketRef.current = socket;

      socket.onopen = () => {
        if (socketRef.current !== socket) {
          return;
        }
        const attach = new AttachAddon(socket, {
          bidirectional: socketConfigRef.current.attachBidirectional,
        });
        addonsRef.current.attach = attach;
        term.loadAddon(attach);
        sendResize();
        fire(handlersRef, "onSocketOpen", resolved);
      };

      socket.onclose = (event) => {
        if (socketRef.current !== socket) {
          return;
        }
        socketRef.current = null;
        fire(handlersRef, "onSocketClose", event.code, event.reason || "");
        if (socketConfigRef.current.reconnect && mountedRef.current) {
          reconnectTimerRef.current = setTimeout(
            () => openSocket(url),
            socketConfigRef.current.reconnectDelayMs,
          );
        }
      };

      socket.onerror = () => {
        fire(handlersRef, "onSocketError", "websocket error");
      };
    },
    [closeSocket, sendResize],
  );

  /* ------------------------------------------------------------------ */
  /* Addon loading                                                       */
  /* ------------------------------------------------------------------ */

  const loadAddons = useCallback(
    (term, requested) => {
      const loaded = addonsRef.current;

      const add = (name, factory) => {
        if (loaded[name] || loaded[`__failed_${name}`]) {
          return loaded[name] || null;
        }
        try {
          const instance = factory();
          term.loadAddon(instance);
          loaded[name] = instance;
          return instance;
        } catch (error) {
          /* Remember the failure so the next render does not retry forever. */
          loaded[`__failed_${name}`] = true;
          console.error(`[reflex-xtermjs] addon "${name}" failed to load`, error);
          return null;
        }
      };

      for (const name of requested || []) {
        switch (name) {
          case "fit":
            add("fit", () => new FitAddon());
            break;
          case "search": {
            const search = add("search", () => new SearchAddon());
            if (search && !loaded.__searchBound) {
              loaded.__searchBound = true;
              disposablesRef.current.push(
                search.onDidChangeResults((event) =>
                  fire(
                    handlersRef,
                    "onSearchResults",
                    event?.resultIndex ?? -1,
                    event?.resultCount ?? 0,
                  ),
                ),
              );
            }
            break;
          }
          case "web-links":
            add(
              "web-links",
              () =>
                new WebLinksAddon((event, uri) => {
                  const handler = handlersRef.current.onLinkClick;
                  if (typeof handler === "function") {
                    handler(uri);
                  } else if (typeof window !== "undefined") {
                    window.open(uri, "_blank", "noopener,noreferrer");
                  }
                }),
            );
            break;
          case "serialize":
            add("serialize", () => new SerializeAddon());
            break;
          case "clipboard":
            add("clipboard", () => new ClipboardAddon());
            break;
          case "unicode11": {
            const unicode = add("unicode11", () => new Unicode11Addon());
            if (unicode) {
              term.unicode.activeVersion = unicodeVersion || "11";
            }
            break;
          }
          case "unicode-graphemes": {
            const graphemes = add(
              "unicode-graphemes",
              () => new UnicodeGraphemesAddon(),
            );
            if (graphemes) {
              term.unicode.activeVersion = unicodeVersion || "15-graphemes";
            }
            break;
          }
          case "image":
            add("image", () => new ImageAddon(imageOptions || {}));
            break;
          case "ligatures":
            add("ligatures", () => new LigaturesAddon(ligatureOptions || {}));
            break;
          case "progress": {
            const progress = add("progress", () => new ProgressAddon());
            if (progress && !loaded.__progressBound) {
              loaded.__progressBound = true;
              disposablesRef.current.push(
                progress.onChange((state) =>
                  fire(
                    handlersRef,
                    "onProgress",
                    state?.state ?? 0,
                    state?.value ?? 0,
                  ),
                ),
              );
            }
            break;
          }
          default:
            console.warn(`[reflex-xtermjs] unknown addon "${name}"`);
        }
      }
    },
    [imageOptions, ligatureOptions, unicodeVersion],
  );

  const loadRenderer = useCallback(
    async (term, which) => {
      const loaded = addonsRef.current;

      /* Drop whichever renderer addon is currently active. */
      for (const key of ["webgl", "canvas"]) {
        if (loaded[key] && key !== which) {
          try {
            loaded[key].dispose();
          } catch (_) {
            /* ignore */
          }
          delete loaded[key];
        }
      }

      if (which === "webgl" && !loaded.webgl) {
        try {
          const webgl = new WebglAddon();
          disposablesRef.current.push(
            webgl.onContextLoss(() => {
              try {
                webgl.dispose();
              } catch (_) {
                /* ignore */
              }
              delete addonsRef.current.webgl;
              fire(handlersRef, "onContextLoss");
            }),
          );
          term.loadAddon(webgl);
          loaded.webgl = webgl;
        } catch (error) {
          console.warn(
            "[reflex-xtermjs] WebGL renderer unavailable, staying on DOM",
            error,
          );
        }
      }

      if (which === "canvas" && !loaded.canvas) {
        try {
          const mod = await import(/* @vite-ignore */ CANVAS_ADDON_PACKAGE);
          const canvas = new mod.CanvasAddon();
          term.loadAddon(canvas);
          loaded.canvas = canvas;
        } catch (error) {
          console.warn(
            "[reflex-xtermjs] canvas renderer unavailable - install " +
              `${CANVAS_ADDON_PACKAGE} to use it; staying on DOM`,
            error,
          );
        }
      }
    },
    [],
  );

  /* ------------------------------------------------------------------ */
  /* Imperative API published for the Reflex backend                     */
  /* ------------------------------------------------------------------ */

  const buildApi = useCallback(
    (term) => ({
      terminal: term,
      addons: addonsRef.current,
      get socket() {
        return socketRef.current;
      },

      write: (data) => term.write(data),
      writeln: (data) => term.writeln(data),
      clear: () => term.clear(),
      reset: () => term.reset(),
      focus: () => term.focus(),
      blur: () => term.blur(),
      refresh: (start, end) => term.refresh(start ?? 0, end ?? term.rows - 1),
      paste: (data) => term.paste(data),
      input: (data, wasUserInput = true) => term.input(data, wasUserInput),
      resize: (c, r) => term.resize(c, r),
      selectAll: () => term.selectAll(),
      select: (column, row, length) => term.select(column, row, length),
      clearSelection: () => term.clearSelection(),
      getSelection: () => term.getSelection(),
      hasSelection: () => term.hasSelection(),
      scrollToTop: () => term.scrollToTop(),
      scrollToBottom: () => term.scrollToBottom(),
      scrollToLine: (line) => term.scrollToLine(line),
      scrollLines: (amount) => term.scrollLines(amount),
      scrollPages: (pages) => term.scrollPages(pages),
      clearTextureAtlas: () => term.clearTextureAtlas(),

      getOption: (name) => term.options[name],
      setOption: (name, value) => {
        term.options[name] = value;
      },
      setOptions: (options) => {
        term.options = { ...term.options, ...(options || {}) };
      },
      getSize: () => ({ cols: term.cols, rows: term.rows }),

      fit: () => {
        const fitAddon = addonsRef.current.fit;
        if (!fitAddon) {
          return null;
        }
        try {
          fitAddon.fit();
        } catch (error) {
          console.warn("[reflex-xtermjs] fit failed", error);
        }
        return { cols: term.cols, rows: term.rows };
      },
      proposeDimensions: () => addonsRef.current.fit?.proposeDimensions() ?? null,

      findNext: (needle, options) =>
        addonsRef.current.search?.findNext(needle, {
          ...(searchOptions || {}),
          ...(options || {}),
        }) ?? false,
      findPrevious: (needle, options) =>
        addonsRef.current.search?.findPrevious(needle, {
          ...(searchOptions || {}),
          ...(options || {}),
        }) ?? false,
      clearSearchDecorations: () => addonsRef.current.search?.clearDecorations(),

      serialize: (options) => addonsRef.current.serialize?.serialize(options) ?? "",
      serializeAsHtml: (options) =>
        addonsRef.current.serialize?.serializeAsHTML(options) ?? "",

      connect: (url) => openSocket(url),
      disconnect: () => closeSocket(),
      send: (data) => {
        const socket = socketRef.current;
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(data);
          return true;
        }
        return false;
      },
      isConnected: () =>
        !!socketRef.current && socketRef.current.readyState === WebSocket.OPEN,

      setRenderer: (which) => loadRenderer(term, which),
      loadAddons: (names) => loadAddons(term, names),
    }),
    [closeSocket, loadAddons, loadRenderer, openSocket, searchOptions],
  );

  /* ------------------------------------------------------------------ */
  /* Mount: create the terminal exactly once                             */
  /* ------------------------------------------------------------------ */

  useEffect(() => {
    if (!containerRef.current) {
      return undefined;
    }
    mountedRef.current = true;

    const term = new Terminal({
      ...collectOptions(props, addons),
      ...(cols ? { cols } : {}),
      ...(rows ? { rows } : {}),
      /* `disableStdin` is the supported way to express a read-only terminal. */
      ...(readOnly ? { disableStdin: true } : {}),
    });
    termRef.current = term;
    term.open(containerRef.current);

    loadAddons(term, addons);
    loadRenderer(term, renderer);

    /* --- event wiring ------------------------------------------------ */
    const d = disposablesRef.current;
    d.push(term.onData((data) => fire(handlersRef, "onData", data)));
    d.push(term.onBinary((data) => fire(handlersRef, "onBinary", data)));
    d.push(
      term.onKey(({ key, domEvent }) =>
        fire(handlersRef, "onKey", key, describeKeyEvent(domEvent)),
      ),
    );
    d.push(
      term.onTitleChange((title) => fire(handlersRef, "onTitleChange", title)),
    );
    d.push(
      term.onResize(({ cols: c, rows: r }) => {
        fire(handlersRef, "onResize", c, r);
        sendResize();
      }),
    );
    d.push(term.onBell(() => fire(handlersRef, "onBell")));
    d.push(term.onLineFeed(() => fire(handlersRef, "onLineFeed")));
    d.push(term.onCursorMove(() => fire(handlersRef, "onCursorMove")));
    d.push(term.onScroll((position) => fire(handlersRef, "onScroll", position)));
    d.push(
      term.onSelectionChange(() =>
        fire(handlersRef, "onSelectionChange", term.getSelection()),
      ),
    );
    d.push(
      term.onRender(({ start, end }) =>
        fire(handlersRef, "onRender", start, end),
      ),
    );
    d.push(term.onWriteParsed(() => fire(handlersRef, "onWriteParsed")));

    /* --- imperative API ---------------------------------------------- */
    const api = buildApi(term);
    registry()[terminalId] = api;

    /* --- auto fit ----------------------------------------------------- */
    let resizeObserver;
    let fitTimer;
    const scheduleFit = () => {
      clearTimeout(fitTimer);
      fitTimer = setTimeout(() => {
        if (!mountedRef.current) {
          return;
        }
        api.fit();
      }, fitDebounceMs);
    };

    if (autoFit && typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(scheduleFit);
      resizeObserver.observe(containerRef.current);
      /* First fit after the browser has laid the container out. */
      requestAnimationFrame(() => api.fit());
    }

    if (initialText) {
      term.write(initialText);
    }
    if (websocketUrl) {
      openSocket(websocketUrl);
    }

    fire(handlersRef, "onReady", term.cols, term.rows);

    return () => {
      mountedRef.current = false;
      clearTimeout(fitTimer);
      resizeObserver?.disconnect();
      closeSocket();
      for (const disposable of disposablesRef.current) {
        try {
          disposable.dispose();
        } catch (_) {
          /* ignore */
        }
      }
      disposablesRef.current = [];
      for (const addon of Object.values(addonsRef.current)) {
        if (addon && typeof addon.dispose === "function") {
          try {
            addon.dispose();
          } catch (_) {
            /* ignore */
          }
        }
      }
      addonsRef.current = {};
      delete registry()[terminalId];
      term.dispose();
      termRef.current = null;
    };
    /* Deliberately mount-only: option changes are handled by the effects below. */
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terminalId]);

  /* ------------------------------------------------------------------ */
  /* Reactive prop syncing                                               */
  /* ------------------------------------------------------------------ */

  /* Terminal options (theme, font, cursor, ...) are patched in place. */
  useLayoutEffect(() => {
    const term = termRef.current;
    if (!term) {
      return;
    }
    const next = collectOptions(props, addons);
    if (readOnly !== undefined) {
      next.disableStdin = !!readOnly || !!props.disableStdin;
    }
    for (const [key, value] of Object.entries(next)) {
      try {
        if (JSON.stringify(term.options[key]) !== JSON.stringify(value)) {
          term.options[key] = value;
        }
      } catch (error) {
        console.warn(`[reflex-xtermjs] could not set option "${key}"`, error);
      }
    }
    addonsRef.current.fit?.fit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(collectOptions(props, addons)), readOnly]);

  /* Addon set. */
  useEffect(() => {
    const term = termRef.current;
    if (term) {
      loadAddons(term, addons);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(addons)]);

  /* Renderer. */
  useEffect(() => {
    const term = termRef.current;
    if (term) {
      loadRenderer(term, renderer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [renderer]);

  /* Explicit size, when the app is not auto-fitting. */
  useEffect(() => {
    const term = termRef.current;
    if (term && !autoFit && cols && rows) {
      term.resize(cols, rows);
    }
  }, [autoFit, cols, rows]);

  /* WebSocket endpoint. */
  useEffect(() => {
    if (!termRef.current) {
      return;
    }
    if (websocketUrl) {
      openSocket(websocketUrl);
    } else {
      closeSocket();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [websocketUrl]);

  return (
    <div
      ref={containerRef}
      id={rest.id}
      className={className}
      style={{ width: "100%", height: "100%", ...(style || {}) }}
      data-terminal-id={terminalId}
    />
  );
}

export default XTerm;
