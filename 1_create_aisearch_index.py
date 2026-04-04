import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("【Index登録】")

from azure.core.credentials import AzureKeyCredential

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField, SearchableField, SearchField, SearchFieldDataType, SemanticField,
    LexicalAnalyzerName,
    VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration,
    SemanticConfiguration, SemanticSearch, SemanticPrioritizedFields,
    CorsOptions
)

# AI Searchクライアント
aisearch_index_client = SearchIndexClient(
    endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
    credential=AzureKeyCredential(key=os.getenv("AZURE_AI_SEARCH_ADMIN_API_KEY"))
)

aisearch_index_name = os.getenv("AZURE_AI_SEARCH_INDEX_NAME", "test_index")

#==================================================
# インデックス作成
#==================================================
def create_index():
    index = SearchIndex(
        name=aisearch_index_name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(
                name="filename", 
                type=SearchFieldDataType.String,
                sortable=True,
                analyzer_name=LexicalAnalyzerName.JA_MICROSOFT
            ),
            SimpleField(
                name="filepath",
                type=SearchFieldDataType.String
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name=LexicalAnalyzerName.JA_MICROSOFT
            ),
            SearchableField(
                name="category",
                type=SearchFieldDataType.String,
                collection=True,
                analyzer_name=LexicalAnalyzerName.JA_MICROSOFT,
                facetable=True,
                filterable=True,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=3072,
                vector_search_profile_name="vector-profile"
            )
        ],
        # CORS設定
        cors_options=CorsOptions(
            allowed_origins=["*"],
            max_age_in_seconds=300,  # キャッシュ時間
        ),
        # ベクトル検索設定
        vector_search=VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    kind="hnsw",
                    parameters={
                        "m": 16,
                        "efConstruction": 400,
                        "efSearch": 200,
                        "metric": "cosine"
                    }
                )
            ]
        ),
        # セマンティック構成
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name="semantic-config",
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="filename"),
                        content_fields=[
                            SemanticField(field_name="content")
                        ],
                        keywords_fields=[
                            SemanticField(field_name="category")
                        ]
                    )
                )
            ]
        )
    )  # 以上index定義
    
    try:
        aisearch_index_client.create_or_update_index(index)
        logger.info(f"Index {aisearch_index_name} created/updated successfully.")
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise
    
#==================================================
# インデックス削除
#==================================================
def delete_index():
    try:
        aisearch_index_client.delete_index(aisearch_index_name)
        logger.info(f"Index {aisearch_index_name} deleted successfully.")
    except Exception as e:
        logger.error(f"Error deleteing index: {e}")
        
#==================================================
# エントリポイント
#==================================================
if __name__ == "__main__":
    # 冪等にする
    delete_index()
    create_index()
    
    logger.info("✅️ Index Created completely.")