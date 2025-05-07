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
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class HttpClientEmbeddings {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @SuppressWarnings("unchecked") // For casting generic Maps
    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName(); // e.g., "text-embedding-ada-002"

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Embeddings Example --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        List<String> textsToEmbed = Arrays.asList(
                "The sun shines brightly in the clear blue sky.",
                "Machine learning models require vast amounts of data."
        );

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("input", textsToEmbed);
        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } else {
            System.out.println("No embedding model specified in .env, using 'text-embedding-ada-002'.");
            requestBodyMap.put("model", "text-embedding-ada-002"); 
        }
        // Optional: encoding_format (e.g., "float" or "base64")
        // requestBodyMap.put("encoding_format", "float");
        // Optional: dimensions (for newer models that support dimensionality reduction)
        // requestBodyMap.put("dimensions", 256);

        String requestBodyJson;
        try {
            requestBodyJson = objectMapper.writeValueAsString(requestBodyMap);
        } catch (JsonProcessingException e) {
            System.err.println("Error creating JSON request body: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // The endpoint for embeddings is usually /v1/embeddings
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiBaseUrl + "/embeddings")) 
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(requestBodyJson))
                .timeout(Duration.ofSeconds(30))
                .build();

        System.out.println("Requesting embeddings using model: " + requestBodyMap.get("model"));
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            System.out.println("--- API Response (Embeddings) --- ");
            System.out.println("Status Code: " + response.statusCode());
            System.out.println("Body: " + response.body());
            System.out.println("------------------------------------");

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                System.out.println("Model used: " + responseMap.get("model"));
                // Map<String, Object> usage = (Map<String, Object>) responseMap.get("usage");
                // if (usage != null) {
                //    System.out.println("Usage: Prompt Tokens: " + usage.get("prompt_tokens") + ", Total Tokens: " + usage.get("total_tokens"));
                // }

                List<Map<String, Object>> data = (List<Map<String, Object>>) responseMap.get("data");
                if (data != null) {
                    for (int i = 0; i < data.size(); i++) {
                        Map<String, Object> embeddingData = data.get(i);
                        System.out.println("\nEmbedding for input text #" + (i + 1) + ":");
                        System.out.println("Original Text: " + textsToEmbed.get(i));
                        System.out.println("Object Type: " + embeddingData.get("object"));
                        System.out.println("Index: " + embeddingData.get("index"));
                        List<Double> vector = (List<Double>) embeddingData.get("embedding");
                        System.out.println("Vector dimension: " + (vector != null ? vector.size() : "N/A"));
                        System.out.println("Vector (first 5 elements): " + 
                            (vector != null && vector.size() > 5 ? vector.subList(0, 5) + "..." : vector));
                    }
                }
            } else {
                System.err.println("Embedding request failed.");
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("HTTP Client Embeddings example complete.");
    }
} 