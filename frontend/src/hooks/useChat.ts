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

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const currentResponseRef = useRef("");

  // WebSocket を初期化（ページロード時に1回だけ）
  useEffect(() => {
    const apiBase =
      (typeof window !== "undefined" &&
        // Next.js embeds NEXT_PUBLIC_ vars at build time
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).__NEXT_DATA__?.runtimeConfig?.NEXT_PUBLIC_API_URL) ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8001";
    const wsUrl = apiBase.replace(/^http/, "ws") + "/api/chat/ws";

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("Chat WebSocket connected");
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "routing") {
        setAgentInfo({ agent: msg.agent, decision: msg.decision });
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
      }
    };

    ws.onclose = () => {
      console.log("Chat WebSocket closed");
      wsRef.current = null;
      setIsLoading(false);
    };

    ws.onerror = () => {
      console.log("Chat WebSocket error");
      wsRef.current = null;
      setIsLoading(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = useCallback((content: string) => {
    setMessages((prev) => [...prev, { role: "user", content }]);
    setIsLoading(true);
    currentResponseRef.current = "";

    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "message", content }));
    } else {
      // WebSocket が切断されていたら再接続
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const wsUrl = apiBase.replace(/^http/, "ws") + "/api/chat/ws";
      const newWs = new WebSocket(wsUrl);
      wsRef.current = newWs;

      newWs.onopen = () => {
        newWs.send(JSON.stringify({ type: "message", content }));
      };

      newWs.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "routing") {
          setAgentInfo({ agent: msg.agent, decision: msg.decision });
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
        }
      };

      newWs.onclose = () => {
        setIsLoading(false);
        wsRef.current = null;
      };
      newWs.onerror = () => {
        setIsLoading(false);
        wsRef.current = null;
      };
    }
  }, []);

  return { messages, isLoading, agentInfo, sendMessage };
}
