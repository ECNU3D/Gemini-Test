package com.example.basic_inference;

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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class HttpClientStream {

    // Pattern to extract the JSON part of an SSE event
    private static final Pattern SSE_DATA_PATTERN = Pattern.compile("data: (.*)");

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Streaming Chat Completion --- ");

        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        ObjectMapper objectMapper = new ObjectMapper();
        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");
        message.put("content", "Tell me a short story about a brave robot. Make it at least 5 sentences long.");

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", List.of(message));
        requestBodyMap.put("temperature", 0.7);
        requestBodyMap.put("stream", true); // Enable streaming
        if (modelName != null) {
            requestBodyMap.put("model", modelName);
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
                .header("Accept", "text/event-stream") // Important for SSE
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofSeconds(60)) // Longer timeout for streaming
                .build();

        System.out.println("Sending streaming request to: " + request.uri());
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");
        System.out.println("Streaming Response:");

        try {
            HttpResponse<java.io.InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
                    String line;
                    StringBuilder fullResponse = new StringBuilder();
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data:")) {
                            String jsonData = line.substring(5).trim(); // Remove "data: " prefix
                            if ("[DONE]".equalsIgnoreCase(jsonData)) {
                                System.out.println("\nStream finished (saw [DONE] message).");
                                break;
                            }
                            try {
                                Map<String, Object> chunkMap = objectMapper.readValue(jsonData, Map.class);
                                List<Map<String, Object>> choices = (List<Map<String, Object>>) chunkMap.get("choices");
                                if (choices != null && !choices.isEmpty()) {
                                    Map<String, Object> firstChoice = choices.get(0);
                                    Map<String, String> delta = (Map<String, String>) firstChoice.get("delta");
                                    if (delta != null && delta.containsKey("content")) {
                                        String content = delta.get("content");
                                        System.out.print(content);
                                        fullResponse.append(content);
                                    }
                                }
                            } catch (JsonProcessingException e) {
                                System.err.println("\nError parsing JSON chunk: " + jsonData + " - " + e.getMessage());
                            } catch (ClassCastException e) {
                                System.err.println("\nError processing chunk structure: " + jsonData + " - " + e.getMessage());
                            }
                        } else if (!line.trim().isEmpty()){
                            // System.out.println("Received non-data line: " + line); // For debugging SSE protocol
                        }
                    }
                    System.out.println("\n------------------------------------");
                    System.out.println("Full Streamed Assistant Response:");
                    System.out.println(fullResponse.toString());
                }
            } else {
                System.err.println("Request failed with status code: " + response.statusCode());
                // Attempt to read error body if present
                try (BufferedReader errorReader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
                    String errorLine;
                    StringBuilder errorBody = new StringBuilder();
                    while ((errorLine = errorReader.readLine()) != null) {
                        errorBody.append(errorLine).append(System.lineSeparator());
                    }
                     System.err.println("Error Body: " + errorBody.toString());
                } catch (IOException ex) {
                    System.err.println("Could not read error stream: " + ex.getMessage());
                }
            }
            System.out.println("------------------------------------");

        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("Streaming HTTP client example complete.");
    }
} 