package org.copperkettle.faq;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import io.quarkiverse.langchain4j.RegisterAiService;

/** The LLM-facing contract. Retrieved FAQ chunks are injected by the RetrievalAugmentor bean. */
@RegisterAiService
public interface BrewingAssistant {

    @SystemMessage("""
            You are the Copperkettle Homebrew Club FAQ assistant.
            Answer only from the context provided with the question, in at most three sentences.
            If the context does not contain the answer, reply exactly: "I don't know - ask a club mentor."
            """)
    @UserMessage("{question}")
    String answer(String question);
}
