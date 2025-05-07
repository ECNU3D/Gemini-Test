package com.example.concurrent_inference;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionChunk;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.service.OpenAiService;

import io.reactivex.Flowable;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkConcurrentStream {

    private static final int NUMBER_OF_REQUESTS = 3; // Keep low for concurrent streams demo

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Concurrent Streaming Chat Completions --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(60))
                    .newBuilder().build(); // Longer timeout for streams
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
                System.out.println("Using custom API base URL: " + apiBaseUrl);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(60));
                System.out.println("Using default OpenAI API base URL.");
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        ExecutorService executorService = Executors.newFixedThreadPool(NUMBER_OF_REQUESTS > 0 ? NUMBER_OF_REQUESTS : 1);
        List<CompletableFuture<Void>> futures = new ArrayList<>();
        AtomicInteger successfulStreams = new AtomicInteger(0);
        AtomicInteger failedStreams = new AtomicInteger(0);

        System.out.println("Submitting " + NUMBER_OF_REQUESTS + " concurrent streaming requests...");

        for (int i = 0; i < NUMBER_OF_REQUESTS; i++) {
            final int requestId = i + 1;
            CompletableFuture<Void> future = CompletableFuture.runAsync(() -> {
                System.out.println("[Stream-" + requestId + "] Starting request...");
                List<ChatMessage> messages = new ArrayList<>();
                messages.add(new ChatMessage(ChatMessageRole.USER.value(), 
                    "Tell me a very short story (2-3 sentences). Request ID: " + requestId));

                ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                        .messages(messages)
                        .temperature(0.6 + (requestId * 0.1))
                        .stream(true)
                        .n(1);

                if (modelName != null && !modelName.isEmpty()) {
                    requestBuilder.model(modelName);
                } else {
                    requestBuilder.model("gpt-3.5-turbo");
                }
                ChatCompletionRequest request = requestBuilder.build();
                StringBuilder responseBuilder = new StringBuilder();

                try {
                    Flowable<ChatCompletionChunk> flowable = service.streamChatCompletion(request);
                    
                    // Non-blocking subscription
                    CompletableFuture<Void> streamCompletionFuture = new CompletableFuture<>();
                    flowable.subscribe(
                        chunk -> {
                            if (chunk.getChoices() != null && !chunk.getChoices().isEmpty()) {
                                ChatMessage chunkMessage = chunk.getChoices().get(0).getMessage();
                                if (chunkMessage != null && chunkMessage.getContent() != null) {
                                    String content = chunkMessage.getContent();
                                    System.out.print("[Stream-" + requestId + "]: " + content.replace("\n", "\\n"));
                                    responseBuilder.append(content);
                                }
                            }
                        },
                        error -> {
                            System.err.println("\n[Stream-" + requestId + "] Error during streaming: " + error.getMessage());
                            // error.printStackTrace(); // For more details
                            failedStreams.incrementAndGet();
                            streamCompletionFuture.completeExceptionally(error);
                        },
                        () -> {
                            System.out.println("\n[Stream-" + requestId + "] Stream completed.");
                            System.out.println("[Stream-" + requestId + "] Full Response: " + responseBuilder.toString().replace("\n", "\\n"));
                            successfulStreams.incrementAndGet();
                            streamCompletionFuture.complete(null);
                        }
                    );
                    streamCompletionFuture.join(); // Wait for this specific stream to complete

                } catch (Exception e) {
                    System.err.println("\n[Stream-" + requestId + "] Failed to initiate stream: " + e.getMessage());
                    failedStreams.incrementAndGet();
                }
            }, executorService);
            futures.add(future);
        }

        System.out.println("\n--- Waiting for all concurrent streaming tasks to complete their setup and processing ---");
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        System.out.println("\n--- All Concurrent Streaming Tasks Finished --- ");
        System.out.println("Successful streams: " + successfulStreams.get());
        System.out.println("Failed streams: " + failedStreams.get());

        executorService.shutdown();
        service.shutdownExecutor();
        System.out.println("\nConcurrent SDK streaming example complete.");
    }
} 