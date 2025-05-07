package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
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

public class HttpClientAdvancedStream {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Advanced Streaming --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1) 
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        Map<String, Object> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", "Explain the concept of neural networks in detail, like you are teaching a beginner. Include at least 3 sections.");
        
        List<Map<String, Object>> messages = new ArrayList<>();
        messages.add(userMessage);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("temperature", 0.7);
        requestBodyMap.put("stream", true);
        // requestBodyMap.put("stream_options", Map.of("include_usage", true)); // If API supports this for final usage stats

        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } else {
            requestBodyMap.put("model", "gpt-3.5-turbo");
        }

        String requestBodyJson;
        try {
            requestBodyJson = objectMapper.writeValueAsString(requestBodyMap);
        } catch (JsonProcessingException e) {
            System.err.println("Error creating JSON request body: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiBaseUrl + "/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Accept", "text/event-stream")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofMinutes(3)) // Longer timeout for potentially long streams
                .build();

        System.out.println("Sending advanced streaming request...");
        System.out.println("------------------------------------");
        StringBuilder fullResponseContent = new StringBuilder();
        boolean streamErrorOccurred = false;

        try {
            HttpResponse<InputStream> response = httpClient.send(request, HttpResponse.BodyHandlers.ofInputStream());

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data:")) {
                            String jsonData = line.substring(5).trim();
                            if ("[DONE]".equalsIgnoreCase(jsonData)) {
                                System.out.println("\nStream marked [DONE].");
                                break; 
                            }
                            try {
                                Map<String, Object> chunkMap = objectMapper.readValue(jsonData, Map.class);
                                // System.out.println("Raw Chunk: " + chunkMap); // For debugging

                                List<Map<String, Object>> choices = (List<Map<String, Object>>) chunkMap.get("choices");
                                if (choices != null && !choices.isEmpty()) {
                                    Map<String, Object> choice = choices.get(0);
                                    Map<String, Object> delta = (Map<String, Object>) choice.get("delta");
                                    if (delta != null && delta.containsKey("content")) {
                                        String content = (String) delta.get("content");
                                        System.out.print(content);
                                        fullResponseContent.append(content);
                                    }
                                    if (choice.containsKey("finish_reason")) {
                                        System.out.println("\nFinish Reason in chunk: " + choice.get("finish_reason"));
                                    }
                                }
                                // Check for usage statistics if API includes it in the stream (often in the last data event before DONE)
                                if (chunkMap.containsKey("usage")) {
                                    Map<String, Object> usage = (Map<String, Object>) chunkMap.get("usage");
                                    System.out.println("\nUsage data received in stream: " + usage);
                                }

                            } catch (JsonProcessingException e) {
                                System.err.println("\nError parsing JSON chunk: " + jsonData + "\n" + e.getMessage());
                            }
                        } else if (line.startsWith("event:")) {
                            System.out.println("\nReceived SSE event: " + line);
                            // Potentially handle custom events like 'error' if the API sends them this way
                        } else if (!line.trim().isEmpty()) {
                            // System.out.println("SSE non-data line: " + line); // Other SSE protocol lines
                        }
                    }
                }
            } else {
                streamErrorOccurred = true;
                System.err.println("HTTP Error: " + response.statusCode());
                try (InputStream errorStream = response.body()) {
                    String errorBody = new String(errorStream.readAllBytes(), StandardCharsets.UTF_8);
                    System.err.println("Error Body: " + errorBody);
                } catch (IOException e) {
                    System.err.println("Could not read error stream body: " + e.getMessage());
                }
            }
        } catch (IOException | InterruptedException e) {
            streamErrorOccurred = true;
            System.err.println("\nError during HTTP request/stream: " + e.getMessage());
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            // e.printStackTrace();
        }

        System.out.println("\n------------------------------------");
        if (!streamErrorOccurred) {
            System.out.println("Full Streamed Response Content:");
            System.out.println(fullResponseContent.toString());
        } else {
            System.out.println("Stream had errors or failed. Partial content (if any):");
            System.out.println(fullResponseContent.toString());
        }
        System.out.println("------------------------------------");
        System.out.println("HTTP Client Advanced Streaming example complete.");
    }
} 