// ============================================================================
// templates/upsert_graph.cypher
// ----------------------------------------------------------------------------
// 検証済み {nodes, relationships} グラフを単一トランザクションで UPSERT する。
// APOC が使えない環境の場合は、末尾の代替パターン（FOREACH 展開版）を参照。
//
// 入力パラメータ:
//   $graph = {
//     nodes: [
//       {
//         temp_id: "c1",
//         label: "Client",
//         mergeKey: {name: "山田太郎"},  // MERGE 対象の場合のみ
//         properties: {name: "山田太郎", dob: "1995-03-15"}
//       },
//       ...
//     ],
//     relationships: [
//       {
//         source_temp_id: "c1",
//         target_temp_id: "ng1",
//         type: "MUST_AVOID",
//         properties: {}
//       },
//       ...
//     ]
//   }
// ============================================================================

// -----------------------------------------------------------------------
// Version A: APOC あり版（推奨）
// -----------------------------------------------------------------------
// 前提: apoc.merge.node / apoc.merge.relationship が使えること。
// ※注意: label と relationship type はパラメータ化できないが、
//   apoc.merge.node は label 配列、apoc.merge.relationship は
//   relationship type 文字列を受け取れる。
//   ALLOWED_LABELS / ALLOWED_REL_TYPES で事前検証済みであることが前提。

// ノード UPSERT
CALL {
  WITH $graph AS g
  UNWIND g.nodes AS n
  CALL apoc.merge.node(
    [n.label],
    CASE WHEN n.mergeKey IS NULL THEN n.properties ELSE n.mergeKey END,
    n.properties,
    n.properties
  ) YIELD node AS created
  RETURN collect({tempId: n.temp_id, elementId: elementId(created)}) AS nodeMap
}

// temp_id → elementId のマップを構築
WITH nodeMap,
     apoc.map.fromLists(
       [m IN nodeMap | m.tempId],
       [m IN nodeMap | m.elementId]
     ) AS idLookup,
     $graph AS g

// リレーション UPSERT
UNWIND g.relationships AS rel
MATCH (src) WHERE elementId(src) = idLookup[rel.source_temp_id]
MATCH (tgt) WHERE elementId(tgt) = idLookup[rel.target_temp_id]
CALL apoc.merge.relationship(
  src,
  rel.type,
  rel.properties,
  rel.properties,
  tgt,
  rel.properties
) YIELD rel AS createdRel

RETURN count(createdRel) AS relationshipsCreated,
       size(nodeMap) AS nodesProcessed;


// -----------------------------------------------------------------------
// Version B: APOC なし版（フォールバック・ラベル固定展開）
// -----------------------------------------------------------------------
// ALLOWED_LABELS が有限のため、ラベルごとに静的展開する方式。
// 以下は Client と SupportLog の例。実運用では全 17 ラベル分を展開すること。
// 本ファイルでは代表例のみ示す。
//
// // Client（MERGE）
// UNWIND [n IN $graph.nodes WHERE n.label = "Client"] AS n
// MERGE (c:Client {name: n.mergeKey.name})
// SET c += n.properties
// WITH n, c
// ... 続く（temp_id を node に記録する一時プロパティ手法が必要）
//
// 詳細は scripts/static_upsert_generator.py で全ラベル分を自動生成すること。
