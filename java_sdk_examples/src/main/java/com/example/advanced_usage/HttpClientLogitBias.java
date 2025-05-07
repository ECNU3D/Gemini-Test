package com.example.advanced_usage;

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

public class HttpClientLogitBias {
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

        System.out.println("--- Java HTTP Client Logit Bias Example --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        List<Map<String, String>> messages = new ArrayList<>();
        Map<String, String> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", "Describe a common pet. Please avoid the word 'dog'.");
        messages.add(userMessage);

        // Logit bias: Strongly decrease the probability of the token for "dog"
        // IMPORTANT: Token IDs are model-specific. '13070' is just an illustrative example.
        // You would need to use a tokenizer for your specific model to find the correct ID for "dog".
        Map<String, Integer> logitBias = new HashMap<>();
        logitBias.put("13070", -100); // Example token ID for "dog", make very unlikely
        // logitBias.put("dog", -100); // Some APIs might allow string keys directly for convenience
        
        System.out.println("Note: Logit bias token IDs are model-specific. The ID '13070' is illustrative.");

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("temperature", 0.7);
        requestBodyMap.put("logit_bias", logitBias);

        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } else {
            System.out.println("No model specified, using 'gpt-3.5-turbo'.");
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
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofSeconds(30))
                .build();

        System.out.println("Sending request with logit bias...");
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            System.out.println("--- API Response --- ");
            System.out.println("Status Code: " + response.statusCode());
            System.out.println("Body: " + response.body());
            System.out.println("------------------------------------");

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                if (choices != null && !choices.isEmpty()) {
                    Map<String, String> responseMessage = (Map<String, String>) choices.get(0).get("message");
                    System.out.println("Assistant Message: " + responseMessage.get("content"));
                }
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("HTTP Client Logit Bias example complete.");
    }
} 