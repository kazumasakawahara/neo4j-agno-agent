"use client";
import { useCallback, useEffect, useRef, useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface AgentInfo {
  agent: string;
  decision: string;
}

/** WebSocket 再接続の最大リトライ回数 */
const MAX_RECONNECT_ATTEMPTS = 3;

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const currentResponseRef = useRef("");
  const reconnectCountRef = useRef(0);

  // ----------------------------------------------------------------
  // 共通: WebSocket メッセージ処理（JSON.parse を try/catch で保護）
  // ----------------------------------------------------------------
  const handleWsMessage = useCallback((event: MessageEvent) => {
    let msg: { type?: string; content?: string; agent?: string; decision?: string };
    try {
      msg = JSON.parse(event.data);
    } catch {
      console.warn("WebSocket: 不正な JSON を受信:", event.data);
      return; // 壊れたメッセージは無視
    }

    if (msg.type === "routing") {
      setAgentInfo({ agent: msg.agent ?? "", decision: msg.decision ?? "" });
    } else if (msg.type === "stream") {
      currentResponseRef.current += msg.content || "";
      const text = currentResponseRef.current;
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "assistant") {
          return [...prev.slice(0, -1), { role: "assistant", content: text }];
        }
        return [...prev, { role: "assistant", content: text }];
      });
    } else if (msg.type === "done") {
      currentResponseRef.current = "";
      setIsLoading(false);
      setAgentInfo(null);
    } else if (msg.type === "error") {
      // サーバー側から返されるエラーメッセージ
      setError(msg.content || "サーバーエラーが発生しました");
      setIsLoading(false);
    }
  }, []);

  // ----------------------------------------------------------------
  // 共通: WebSocket close/error ハンドラ
  // ----------------------------------------------------------------
  const handleWsClose = useCallback(() => {
    console.log("Chat WebSocket closed");
    wsRef.current = null;
    setIsLoading(false);
  }, []);

  const handleWsError = useCallback(() => {
    console.warn("Chat WebSocket error");
    wsRef.current = null;
    setIsLoading(false);
  }, []);

  // ----------------------------------------------------------------
  // WebSocket 初期化（ページロード時に1回だけ）
  // ----------------------------------------------------------------
  useEffect(() => {
    const apiBase =
      (typeof window !== "undefined" &&
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).__NEXT_DATA__?.runtimeConfig?.NEXT_PUBLIC_API_URL) ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8001";
    const wsUrl = apiBase.replace(/^http/, "ws") + "/api/chat/ws";

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => {
        console.log("Chat WebSocket connected");
        reconnectCountRef.current = 0;
        setError(null);
      };
      ws.onmessage = handleWsMessage;
      ws.onclose = handleWsClose;
      ws.onerror = handleWsError;

      return () => {
        ws.close();
      };
    } catch (e) {
      console.error("WebSocket の初期化に失敗:", e);
      setError("チャットサーバーに接続できませんでした");
      return undefined;
    }
  }, [handleWsMessage, handleWsClose, handleWsError]);

  // ----------------------------------------------------------------
  // メッセージ送信（切断時は再接続を試みる）
  // ----------------------------------------------------------------
  const sendMessage = useCallback(
    (content: string) => {
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content }]);
      setIsLoading(true);
      currentResponseRef.current = "";

      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "message", content }));
        return;
      }

      // --- 再接続 ---
      if (reconnectCountRef.current >= MAX_RECONNECT_ATTEMPTS) {
        setError("チャットサーバーとの接続が切れました。ページを再読み込みしてください。");
        setIsLoading(false);
        return;
      }
      reconnectCountRef.current += 1;

      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const wsUrl = apiBase.replace(/^http/, "ws") + "/api/chat/ws";

      try {
        const newWs = new WebSocket(wsUrl);
        wsRef.current = newWs;

        newWs.onopen = () => {
          reconnectCountRef.current = 0;
          setError(null);
          newWs.send(JSON.stringify({ type: "message", content }));
        };
        newWs.onmessage = handleWsMessage;
        newWs.onclose = handleWsClose;
        newWs.onerror = () => {
          handleWsError();
          setError("チャットサーバーに再接続できませんでした");
        };
      } catch (e) {
        console.error("WebSocket 再接続失敗:", e);
        setError("チャットサーバーに再接続できませんでした");
        setIsLoading(false);
      }
    },
    [handleWsMessage, handleWsClose, handleWsError],
  );

  /** エラー状態をクリアする */
  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, agentInfo, error, sendMessage, clearError };
}
