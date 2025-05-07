package com.example.concurrent_inference;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatCompletionChoice;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.service.OpenAiService;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkConcurrentNormal {

    private static final int NUMBER_OF_REQUESTS = 5; // Number of concurrent requests to send

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Concurrent Normal Chat Completions --- ");

        // Create a single OpenAiService instance to be shared across threads
        // The internal OkHttpClient of OpenAiService is designed for concurrency.
        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30))
                    .newBuilder()
                    // Configure connection pool for OkHttpClient if needed for very high concurrency
                    // .connectionPool(new ConnectionPool(10, 5, TimeUnit.MINUTES))
                    .build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
                System.out.println("Using custom API base URL: " + apiBaseUrl);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
                System.out.println("Using default OpenAI API base URL.");
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // Use a fixed-size thread pool for sending requests concurrently
        // Adjust pool size based on expected load and API rate limits
        ExecutorService executorService = Executors.newFixedThreadPool(NUMBER_OF_REQUESTS > 0 ? NUMBER_OF_REQUESTS : 1);
        List<CompletableFuture<String>> futures = new ArrayList<>();

        System.out.println("Submitting " + NUMBER_OF_REQUESTS + " concurrent requests...");

        for (int i = 0; i < NUMBER_OF_REQUESTS; i++) {
            final int requestId = i + 1;
            CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
                System.out.println("Sending request #" + requestId + "...");
                List<ChatMessage> messages = new ArrayList<>();
                messages.add(new ChatMessage(ChatMessageRole.USER.value(), "Tell me a fun fact. Request ID: " + requestId));

                ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                        .messages(messages)
                        .temperature(0.7 + (requestId * 0.05)) // Vary temperature slightly
                        .n(1);

                if (modelName != null && !modelName.isEmpty()) {
                    requestBuilder.model(modelName);
                } else {
                    requestBuilder.model("gpt-3.5-turbo");
                }
                ChatCompletionRequest request = requestBuilder.build();

                try {
                    List<ChatCompletionChoice> choices = service.createChatCompletion(request).getChoices();
                    if (choices != null && !choices.isEmpty()) {
                        String content = choices.get(0).getMessage().getContent();
                        System.out.println("Request #" + requestId + " successful. Response: " + content.substring(0, Math.min(content.length(), 50)) + "...");
                        return "Request #" + requestId + ": " + content;
                    } else {
                        System.err.println("Request #" + requestId + " returned no choices.");
                        return "Request #" + requestId + ": No choices returned.";
                    }
                } catch (Exception e) {
                    System.err.println("Request #" + requestId + " failed: " + e.getMessage());
                    // Optionally, log e.printStackTrace() for more details
                    return "Request #" + requestId + ": Error - " + e.getMessage();
                }
            }, executorService);
            futures.add(future);
        }

        // Wait for all futures to complete
        System.out.println("\n--- Waiting for all concurrent requests to complete --- ");
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        System.out.println("\n--- All Concurrent Requests Completed --- ");

        futures.forEach(future -> {
            try {
                System.out.println(future.get());
            } catch (Exception e) {
                System.err.println("Error retrieving future result: " + e.getMessage());
            }
        });

        executorService.shutdown();
        service.shutdownExecutor(); // Shutdown OpenAiService's internal executor
        System.out.println("\nConcurrent SDK normal example complete.");
    }
} 