"use client";
import { useCallback, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentInfo, setAgentInfo] = useState<{ agent: string; decision: string } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef<string | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    // 接続中の場合はスキップ（pending メッセージは onopen で送信される）
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    const wsUrl = apiBase.replace(/^http/, "ws") + "/api/chat/ws";
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    let currentResponse = "";

    ws.onopen = () => {
      // 接続確立後、保留中のメッセージがあれば送信
      if (pendingRef.current) {
        ws.send(JSON.stringify({ type: "message", content: pendingRef.current }));
        pendingRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      const msg: ChatMessage = JSON.parse(event.data);
      if (msg.type === "routing") {
        setAgentInfo({ agent: msg.agent!, decision: msg.decision! });
      } else if (msg.type === "stream") {
        currentResponse += msg.content || "";
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            return [...updated.slice(0, -1), { ...last, content: currentResponse }];
          }
          return [...updated, { role: "assistant", content: currentResponse }];
        });
      } else if (msg.type === "done") {
        currentResponse = "";
        setIsLoading(false);
        setAgentInfo(null);
      }
    };

    ws.onclose = () => {
      setIsLoading(false);
      wsRef.current = null;
    };

    ws.onerror = () => {
      setIsLoading(false);
      wsRef.current = null;
    };
  }, []);

  const sendMessage = useCallback((content: string) => {
    setMessages((prev) => [...prev, { role: "user", content }]);
    setIsLoading(true);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // 既に接続済み → 即送信
      wsRef.current.send(JSON.stringify({ type: "message", content }));
    } else {
      // 未接続 → 保留して接続開始、onopen で送信される
      pendingRef.current = content;
      connect();
    }
  }, [connect]);

  return { messages, isLoading, agentInfo, sendMessage };
}
