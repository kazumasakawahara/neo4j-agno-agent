"use client";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: api.system.status,
    refetchInterval: 10000,
  });

  const providerLabel = status?.chat_provider === "claude" ? "Claude" : "Gemini";

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">システム設定</h2>

      {/* 接続状態 */}
      <Card>
        <CardHeader><CardTitle className="text-base">接続状態</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Gemini API</span>
            <Badge variant={status?.gemini_available ? "default" : "destructive"}>
              {status?.gemini_available ? "接続中" : "未設定"}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Claude API (Anthropic)</span>
            <Badge variant={status?.claude_available ? "default" : "destructive"}>
              {status?.claude_available ? "接続中" : "未設定"}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Neo4j</span>
            <Badge variant={status?.neo4j_available ? "default" : "destructive"}>
              {status?.neo4j_available ? "接続中" : "未接続"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* チャットプロバイダー */}
      <Card>
        <CardHeader><CardTitle className="text-base">チャット AI</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">使用中のプロバイダー</span>
            <Badge variant="outline">{providerLabel}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">モデル</span>
            <span className="text-sm font-mono">{status?.chat_model || "-"}</span>
          </div>
          <p className="text-xs text-muted-foreground">
            .env の CHAT_PROVIDER で切替（gemini / claude）。API サーバー再起動で反映。
          </p>
        </CardContent>
      </Card>

      {/* Embedding */}
      <Card>
        <CardHeader><CardTitle className="text-base">Embedding</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">モデル</span>
            <span className="text-sm font-mono">{status?.embedding_model || "-"}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Embedding は常に Gemini Embedding 2 を使用（チャットプロバイダーとは独立）。
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
