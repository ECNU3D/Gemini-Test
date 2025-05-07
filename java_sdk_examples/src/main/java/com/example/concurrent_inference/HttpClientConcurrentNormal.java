package com.example.concurrent_inference;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class HttpClientConcurrentNormal {

    private static final int NUMBER_OF_REQUESTS = 5;
    private static final ObjectMapper objectMapper = new ObjectMapper(); // Shared, thread-safe

    // Shared HttpClient for all concurrent requests
    // Configure connection pool for higher concurrency if needed.
    // Default is no limit for HTTP/1.1 and 6 for HTTP/2 per host.
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1) // Or HTTP_2 if endpoint supports
            .connectTimeout(Duration.ofSeconds(10))
            // .executor(Executors.newFixedThreadPool(APPROPRIATE_POOL_SIZE_FOR_HTTP_CLIENT))
            .build();

    @SuppressWarnings("unchecked") // For casting Object to Map
    private static String makeSingleRequest(int requestId, String apiKey, String apiBaseUrl, String modelName) {
        System.out.println("Sending request #" + requestId + " via HTTP Client...");
        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");
        message.put("content", "Tell me a very short fun fact. Request ID: " + requestId);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", List.of(message));
        requestBodyMap.put("temperature", 0.7 + (requestId * 0.05));
        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } // else use endpoint default or ensure model is always set

        String requestBodyJson;
        try {
            requestBodyJson = objectMapper.writeValueAsString(requestBodyMap);
        } catch (JsonProcessingException e) {
            System.err.println("Request #" + requestId + " - Error creating JSON: " + e.getMessage());
            return "Request #" + requestId + ": JSON Error - " + e.getMessage();
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiBaseUrl + "/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofSeconds(25)) // Per-request timeout
                .build();
        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                if (choices != null && !choices.isEmpty()) {
                    Map<String, Object> firstChoiceMessage = (Map<String, Object>) choices.get(0).get("message");
                    if (firstChoiceMessage != null) {
                        String content = (String) firstChoiceMessage.get("content");
                        if (content != null) {
                            System.out.println("Request #" + requestId + " successful. Response: " + content.substring(0, Math.min(content.length(), 50)) + "...");
                            return "Request #" + requestId + ": " + content;
                        }
                    }
                }
                System.err.println("Request #" + requestId + " - No choices or message content in response.");
                return "Request #" + requestId + ": No choices or message content.";
            } else {
                System.err.println("Request #" + requestId + " - Failed with status: " + response.statusCode() + " Body: " + response.body().substring(0, Math.min(response.body().length(), 200)));
                return "Request #" + requestId + ": HTTP Error " + response.statusCode();
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("Request #" + requestId + " - Exception: " + e.getMessage());
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            return "Request #" + requestId + ": Exception - " + e.getMessage();
        }
    }

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Concurrent Normal Chat Completions --- ");
        ExecutorService executorService = Executors.newFixedThreadPool(NUMBER_OF_REQUESTS > 0 ? NUMBER_OF_REQUESTS : 1);
        List<CompletableFuture<String>> futures = new ArrayList<>();

        System.out.println("Submitting " + NUMBER_OF_REQUESTS + " concurrent requests...");

        for (int i = 0; i < NUMBER_OF_REQUESTS; i++) {
            final int requestId = i + 1;
            futures.add(CompletableFuture.supplyAsync(() -> 
                makeSingleRequest(requestId, apiKey, apiBaseUrl, modelName), executorService));
        }

        System.out.println("\n--- Waiting for all concurrent HTTP requests to complete --- ");
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        System.out.println("\n--- All Concurrent HTTP Requests Completed --- ");

        futures.forEach(future -> {
            try {
                System.out.println(future.get());
            } catch (Exception e) {
                System.err.println("Error retrieving future result from HTTP request: " + e.getMessage());
            }
        });

        executorService.shutdown();
        try {
            if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        } catch (InterruptedException e) {
            executorService.shutdownNow();
            Thread.currentThread().interrupt();
        }
        System.out.println("\nConcurrent HTTP client normal example complete.");
    }
} 