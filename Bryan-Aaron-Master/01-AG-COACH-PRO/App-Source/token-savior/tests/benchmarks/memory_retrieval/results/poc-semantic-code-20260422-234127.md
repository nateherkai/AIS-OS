[poc] collected 992 symbols from /root/token-savior/src/token_savior in 1.1s
[poc] embedded 992 symbols in 98.9s (P50 100 ms/sym, 0 empty)

## Retrieval quality on descriptive queries

| Query | Top-1 | Top-1 score | Expect-hit in top-5 |
|---|---|---|---|
| function that removes duplicate memory observation | `_mh_memory_delete` | 0.682 | ❌ |
| convert a plain text into a dense vector embedding | `embed` | 0.673 | ✅ |
| fuse two ranked lists of search results | `rrf_merge` | 0.768 | ✅ |
| detect strongly-connected components in an import  | `ProjectQueryEngine.find_import_cycles` | 0.763 | ✅ |
| backfill missing vector rows for existing observat | `backfill_obs_vectors` | 0.720 | ✅ |

**Hit rate (expect term in top-5): 4/5**

Detailed top-3 per query:

### function that removes duplicate memory observations
  0.682  _mh_memory_delete                                             src/token_savior/server_handlers/memory.py:842
  0.669  _mh_memory_restore                                            src/token_savior/server_handlers/memory.py:1076
  0.669  compute_continuity_score                                      src/token_savior/memory/consistency.py:47

### convert a plain text into a dense vector embedding
  0.673  embed                                                         src/token_savior/memory/embeddings.py:89
  0.666  _mh_memory_vector_reindex                                     src/token_savior/server_handlers/memory.py:473
  0.659  maybe_index_obs                                               src/token_savior/memory/embeddings.py:151

### fuse two ranked lists of search results
  0.768  rrf_merge                                                     src/token_savior/memory/search.py:27
  0.715  ProjectQueryEngine.get_relevance_cluster                      src/token_savior/query_api.py:2115
  0.713  observation_search                                            src/token_savior/memory/observations.py:309

### detect strongly-connected components in an import graph
  0.763  ProjectQueryEngine.find_import_cycles                         src/token_savior/query_api.py:2040
  0.687  _graph_based_test_candidates                                  src/token_savior/impacted_tests.py:287
  0.681  _get_all_imports                                              src/token_savior/cross_project.py:15

### backfill missing vector rows for existing observations
  0.720  backfill_obs_vectors                                          src/token_savior/memory/embeddings.py:183
  0.713  _mh_memory_vector_reindex                                     src/token_savior/server_handlers/memory.py:473
  0.646  dedup_sweep                                                   src/token_savior/memory/dedup.py:105
