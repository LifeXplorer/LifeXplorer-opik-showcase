package org.copperkettle.faq;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.rag.DefaultRetrievalAugmentor;
import dev.langchain4j.rag.RetrievalAugmentor;
import dev.langchain4j.rag.content.retriever.EmbeddingStoreContentRetriever;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Singleton;
import org.eclipse.microprofile.config.inject.ConfigProperty;

public class RetrievalConfig {

    @Singleton
    EmbeddingStore<TextSegment> embeddingStore() {
        return new InMemoryEmbeddingStore<>();
    }

    /** Quarkus wires any RetrievalAugmentor bean into the AI service automatically. */
    @ApplicationScoped
    RetrievalAugmentor retrievalAugmentor(EmbeddingStore<TextSegment> store, EmbeddingModel embeddings,
                                          @ConfigProperty(name = "faq.top-k") int topK,
                                          @ConfigProperty(name = "faq.min-score") double minScore) {
        var retriever = EmbeddingStoreContentRetriever.builder()
                .embeddingStore(store)
                .embeddingModel(embeddings)
                .maxResults(topK)
                .minScore(minScore)
                .build();
        return DefaultRetrievalAugmentor.builder().contentRetriever(retriever).build();
    }
}
