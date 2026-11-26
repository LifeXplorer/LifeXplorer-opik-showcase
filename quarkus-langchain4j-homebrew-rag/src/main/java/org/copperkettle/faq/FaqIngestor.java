package org.copperkettle.faq;

import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.EmbeddingStoreIngestor;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import java.nio.file.Path;
import java.util.List;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

/** Reads docs/*.md at startup, splits them into chunks and embeds them into the in-memory store. */
@ApplicationScoped
public class FaqIngestor {

    private static final Logger LOG = Logger.getLogger(FaqIngestor.class);

    void ingest(@Observes StartupEvent ev, EmbeddingStore<TextSegment> store, EmbeddingModel embeddings,
                @ConfigProperty(name = "faq.docs-dir") String docsDir) {
        List<Document> docs = FileSystemDocumentLoader.loadDocuments(Path.of(docsDir));
        EmbeddingStoreIngestor.builder()
                .documentSplitter(DocumentSplitters.recursive(450, 40))
                .embeddingModel(embeddings)
                .embeddingStore(store)
                .build()
                .ingest(docs);
        LOG.infof("Indexed %d FAQ files from %s", docs.size(), docsDir);
    }
}
