package com.example.concurrent_inference;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class HttpClientConcurrentStream {

    private static final int NUMBER_OF_REQUESTS = 3; // Keep low for concurrent streams demo
    private static final ObjectMapper objectMapper = new ObjectMapper();
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    private static void processSingleStream(int requestId, String apiKey, String apiBaseUrl, String modelName,
                                            AtomicInteger successfulStreams, AtomicInteger failedStreams) {
        System.out.println("[HTTP-Stream-" + requestId + "] Starting request...");
        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");
        message.put("content", "Write a short poem (2-4 lines) about space. Request ID: " + requestId);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", List.of(message));
        requestBodyMap.put("temperature", 0.5 + (requestId * 0.1));
        requestBodyMap.put("stream", true);
        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        }

        String requestBodyJson;
        try {
            requestBodyJson = objectMapper.writeValueAsString(requestBodyMap);
        } catch (JsonProcessingException e) {
            System.err.println("\n[HTTP-Stream-" + requestId + "] Error creating JSON: " + e.getMessage());
            failedStreams.incrementAndGet();
            return;
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiBaseUrl + "/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Accept", "text/event-stream")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofSeconds(60)) // Timeout for the entire stream operation
                .build();
        StringBuilder responseBuilder = new StringBuilder();
        try {
            HttpResponse<java.io.InputStream> response = httpClient.send(request, HttpResponse.BodyHandlers.ofInputStream());

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data:")) {
                            String jsonData = line.substring(5).trim();
                            if ("[DONE]".equalsIgnoreCase(jsonData)) {
                                break; // Stream finished
                            }
                            try {
                                Map<String, Object> chunkMap = objectMapper.readValue(jsonData, Map.class);
                                List<Map<String, Object>> choices = (List<Map<String, Object>>) chunkMap.get("choices");
                                if (choices != null && !choices.isEmpty()) {
                                    Map<String, Object> delta = (Map<String, Object>) choices.get(0).get("delta");
                                    if (delta != null && delta.containsKey("content")) {
                                        String content = (String) delta.get("content");
                                        System.out.print("[HTTP-Stream-" + requestId + "]: " + content.replace("\n", "\\n"));
                                        responseBuilder.append(content);
                                    }
                                }
                            } catch (JsonProcessingException e) {
                                System.err.println("\n[HTTP-Stream-" + requestId + "] Error parsing chunk JSON: " + jsonData + " - " + e.getMessage());
                            }
                        }
                    }
                }
                System.out.println("\n[HTTP-Stream-" + requestId + "] Stream completed successfully.");
                System.out.println("[HTTP-Stream-" + requestId + "] Full Response: " + responseBuilder.toString().replace("\n", "\\n"));
                successfulStreams.incrementAndGet();
            } else {
                System.err.println("\n[HTTP-Stream-" + requestId + "] Failed. Status: " + response.statusCode());
                // Log error body if possible
                try (BufferedReader errorReader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
                    String errorLine;
                    StringBuilder errorBody = new StringBuilder();
                    while ((errorLine = errorReader.readLine()) != null) {
                        errorBody.append(errorLine).append(System.lineSeparator());
                    }
                    System.err.println("[HTTP-Stream-" + requestId + "] Error Body: " + errorBody.toString());
                } catch (IOException ex) {
                    System.err.println("[HTTP-Stream-" + requestId + "] Could not read error stream body: " + ex.getMessage());
                }
                failedStreams.incrementAndGet();
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("\n[HTTP-Stream-" + requestId + "] Exception during request/stream: " + e.getMessage());
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            failedStreams.incrementAndGet();
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

        System.out.println("--- Java HTTP Client Concurrent Streaming Chat Completions --- ");
        ExecutorService executorService = Executors.newFixedThreadPool(NUMBER_OF_REQUESTS > 0 ? NUMBER_OF_REQUESTS : 1);
        List<CompletableFuture<Void>> futures = new ArrayList<>();
        AtomicInteger successfulStreams = new AtomicInteger(0);
        AtomicInteger failedStreams = new AtomicInteger(0);

        System.out.println("Submitting " + NUMBER_OF_REQUESTS + " concurrent streaming requests...");

        for (int i = 0; i < NUMBER_OF_REQUESTS; i++) {
            final int requestId = i + 1;
            futures.add(CompletableFuture.runAsync(() -> 
                processSingleStream(requestId, apiKey, apiBaseUrl, modelName, successfulStreams, failedStreams), executorService));
        }

        System.out.println("\n--- Waiting for all concurrent HTTP streaming tasks to complete --- ");
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        System.out.println("\n--- All Concurrent HTTP Streaming Tasks Finished --- ");
        System.out.println("Successful streams: " + successfulStreams.get());
        System.out.println("Failed streams: " + failedStreams.get());

        executorService.shutdown();
        try {
            if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        } catch (InterruptedException e) {
            executorService.shutdownNow();
            Thread.currentThread().interrupt();
        }
        System.out.println("\nConcurrent HTTP client streaming example complete.");
    }
} 