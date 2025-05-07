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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class HttpClientJson {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client JSON Mode Chat Completion --- ");

        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        ObjectMapper objectMapper = new ObjectMapper();
        List<Map<String, String>> messages = new ArrayList<>();
        Map<String, String> systemMessage = new HashMap<>();
        systemMessage.put("role", "system");
        systemMessage.put("content", "You are a helpful assistant designed to output JSON.");
        messages.add(systemMessage);

        Map<String, String> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", "Provide a JSON object with two keys: 'name' and 'city', for a fictional character.");
        messages.add(userMessage);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("temperature", 0.7);
        
        // For JSON mode, set the response_format parameter
        Map<String, String> responseFormat = new HashMap<>();
        responseFormat.put("type", "json_object");
        requestBodyMap.put("response_format", responseFormat);

        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } else {
            // It's good practice to specify a model that is known to support JSON mode well.
            System.out.println("No model specified in .env, using default. Ensure this model supports JSON mode.");
            // requestBodyMap.put("model", "gpt-3.5-turbo-1106"); // Example model known for better JSON handling
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

        System.out.println("Sending JSON mode request to: " + request.uri());
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");

        try {
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            System.out.println("--- API Response --- ");
            System.out.println("Status Code: " + response.statusCode());
            // System.out.println("Headers: " + response.headers().map());
            System.out.println("Raw Body: " + response.body());
            System.out.println("------------------------------------");

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                String responseBody = response.body();
                try {
                    Map<String, Object> responseMap = objectMapper.readValue(responseBody, Map.class);
                    List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                    if (choices != null && !choices.isEmpty()) {
                        Map<String, Object> firstChoice = choices.get(0);
                        Map<String, String> responseMessage = (Map<String, String>) firstChoice.get("message");
                        if (responseMessage != null && responseMessage.containsKey("content")) {
                            String content = responseMessage.get("content");
                            System.out.println("Assistant Message Content (Raw):\n" + content);
                            // Attempt to parse the content string as JSON
                            try {
                                Object jsonContent = objectMapper.readValue(content, Object.class);
                                System.out.println("Successfully parsed content as JSON:");
                                System.out.println(objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(jsonContent));
                            } catch (JsonProcessingException e) {
                                System.err.println("Could not parse assistant message content as JSON: " + e.getMessage());
                                System.err.println("Model output was: " + content);
                            }
                        } else {
                             System.out.println("No 'content' in assistant's message object.");
                        }
                    } else {
                        System.out.println("No 'choices' found in the response body.");
                    }
                } catch (JsonProcessingException e) {
                    System.err.println("Error parsing main JSON response body: " + e.getMessage());
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
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("HTTP client JSON mode example complete.");
    }
} 