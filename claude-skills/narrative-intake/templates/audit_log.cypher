// ============================================================================
// templates/audit_log.cypher
// ----------------------------------------------------------------------------
// narrative-intake 実行結果を AuditLog として記録する。
// 登録セッションごとに 1 件生成（個別ノードではなくセッション単位）。
//
// 入力パラメータ:
//   $user         : 操作者名
//   $clientName   : 対象クライアント名
//   $sessionId    : セッションID
//   $sourceHash   : 入力ナラティブのSHA256
//   $summary      : 登録サマリー（例: "SupportLog×2, NgAction×1, CarePreference×1"）
//   $warnings     : 検証で落とした項目のリスト（JSON文字列）
//   $safetyCheck  : 安全性チェック結果（"OK" / "Violation:<詳細>"）
// ============================================================================

CREATE (al:AuditLog {
    timestamp: datetime(),
    user: $user,
    action: "NARRATIVE_INTAKE",
    targetType: "MultipleNodes",
    targetName: $summary,
    details: "sourceHash=" + $sourceHash +
             " | warnings=" + $warnings +
             " | safetyCheck=" + $safetyCheck,
    clientName: $clientName,
    sourceHash: $sourceHash,
    sessionId: $sessionId
})
WITH al
OPTIONAL MATCH (c:Client {name: $clientName})
WHERE $clientName <> ''
FOREACH (_ IN CASE WHEN c IS NOT NULL THEN [1] ELSE [] END |
    CREATE (al)-[:AUDIT_FOR]->(c)
)
RETURN al.timestamp AS 記録日時,
       al.action    AS 操作,
       al.targetName AS サマリー;


// ============================================================================
// 個別の重要イベント用（NgAction 追加時など、別途強調記録したい場合）
// ============================================================================
// 使用例: 新規 NgAction が追加されたときに上記とは別に記録する
//
// CREATE (al:AuditLog {
//     timestamp: datetime(),
//     user: $user,
//     action: "CREATE",
//     targetType: "NgAction",
//     targetName: $ngActionLabel,
//     details: "ナラティブ抜粋: " + $narrativeExcerpt +
//              " | riskLevel: " + $riskLevel,
//     clientName: $clientName
// })
// WITH al
// MATCH (c:Client {name: $clientName})
// CREATE (al)-[:AUDIT_FOR]->(c)
// RETURN al.timestamp;
