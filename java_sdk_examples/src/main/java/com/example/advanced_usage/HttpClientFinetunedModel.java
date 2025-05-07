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

public class HttpClientFinetunedModel {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @SuppressWarnings("unchecked") // For casting generic Maps
    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        // The MODEL_NAME env var should be set to your fine-tuned model ID
        String finetunedModelId = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        if (finetunedModelId == null || finetunedModelId.trim().isEmpty() || !finetunedModelId.startsWith("ft:")) {
            System.err.println("ERROR: A fine-tuned model ID is not configured or is invalid.");
            System.err.println("Please set the MODEL_NAME environment variable to your fine-tuned model ID.");
            System.err.println("Example: ft:gpt-3.5-turbo-0613:your-org:custom-suffix:idstring");
            return;
        }

        System.out.println("--- Java HTTP Client Using Fine-tuned Model --- ");
        System.out.println("Using fine-tuned model: " + finetunedModelId);

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        List<Map<String, String>> messages = new ArrayList<>();
        Map<String, String> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        // Craft a prompt that is suitable for your fine-tuned model's specialization
        userMessage.put("content", "Based on its training, what is the primary use case for Product X?");
        messages.add(userMessage);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("model", finetunedModelId); // Specify the fine-tuned model ID
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("temperature", 0.7);

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

        System.out.println("Sending request to fine-tuned model: " + finetunedModelId);
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
                    Map<String, Object> firstChoice = choices.get(0);
                    Map<String, String> responseMessage = (Map<String, String>) firstChoice.get("message");
                    if (responseMessage != null) {
                        System.out.println("Assistant Message: " + responseMessage.get("content"));
                    }
                } else {
                    System.out.println("No choices in response.");
                }
            } else {
                System.err.println("Request failed. Ensure your fine-tuned model ID is correct, deployed, and accessible.");
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("HTTP Client Fine-tuned Model example complete.");
    }
} 