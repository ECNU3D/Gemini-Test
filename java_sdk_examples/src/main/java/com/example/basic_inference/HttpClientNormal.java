package com.example.basic_inference;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class HttpClientNormal {

    public static void main(String[] args) {
        // Load configuration
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String model = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Normal Chat Completion --- ");

        // --- Initialize HTTP Client ---
        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        // --- Prepare API Request Body --- 
        ObjectMapper objectMapper = new ObjectMapper();
        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");
        message.put("content", "What is the capital of France?");

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", List.of(message));
        requestBodyMap.put("temperature", 0.7);
        if (model != null) {
            requestBodyMap.put("model", model); // Only include if model is specified
        }
        // Add other parameters like max_tokens if needed
        // requestBodyMap.put("max_tokens", 50);

        String requestBodyJson;
        try {
            requestBodyJson = objectMapper.writeValueAsString(requestBodyMap);
        } catch (JsonProcessingException e) {
            System.err.println("Error creating JSON request body: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // --- Build HTTP Request --- 
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiBaseUrl + "/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofSeconds(30))
                .build();

        System.out.println("Sending request to: " + request.uri());
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");

        try {
            // --- Send Request & Get Response --- 
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            System.out.println("--- API Response --- ");
            System.out.println("Status Code: " + response.statusCode());
            System.out.println("Headers: " + response.headers().map());
            System.out.println("Body: " + response.body());
            System.out.println("------------------------------------");

            // --- Process Response --- 
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                try {
                    // Parse the JSON response body
                    Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                    List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                    if (choices != null && !choices.isEmpty()) {
                        Map<String, Object> firstChoice = choices.get(0);
                        Map<String, String> responseMessage = (Map<String, String>) firstChoice.get("message");
                        if (responseMessage != null) {
                            System.out.println("Assistant Message: " + responseMessage.get("content"));
                        } else {
                             System.out.println("No 'message' object found in the first choice.");
                        }
                    } else {
                        System.out.println("No 'choices' found in the response body.");
                    }
                } catch (JsonProcessingException e) {
                    System.err.println("Error parsing JSON response body: " + e.getMessage());
                    e.printStackTrace();
                } catch (ClassCastException e) {
                     System.err.println("Error processing response structure: " + e.getMessage());
                     e.printStackTrace();
                }
            } else {
                System.err.println("Request failed with status code: " + response.statusCode());
                System.err.println("Response Body: " + response.body());
            }


        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
             // Handle thread interruption specifically
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("Basic HTTP client example complete.");
    }
} 