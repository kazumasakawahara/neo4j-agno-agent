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

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">システム設定</h2>
      <div className="flex gap-4">
        <Badge variant={status?.gemini_available ? "default" : "destructive"}>
          Gemini API: {status?.gemini_available ? "接続中" : "未設定"}
        </Badge>
        <Badge variant={status?.neo4j_available ? "default" : "destructive"}>
          Neo4j: {status?.neo4j_available ? "接続中" : "未接続"}
        </Badge>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">AI モデル</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">テキスト生成</span>
            <span>{status?.gemini_model || "gemini-2.0-flash"}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Embedding</span>
            <span>{status?.embedding_model || "gemini-embedding-2-preview"}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
