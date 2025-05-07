package com.example.multimodal;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class HttpClientImageInput {

    private static String encodeImageToBase64(String imagePath) throws IOException {
        byte[] imageBytes = Files.readAllBytes(Paths.get(imagePath));
        return Base64.getEncoder().encodeToString(imageBytes);
    }

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName(); // Vision-capable model, e.g., gpt-4-vision-preview

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- Java HTTP Client Image Input (Vision) --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        ObjectMapper objectMapper = new ObjectMapper();
        List<Map<String, Object>> messages = new ArrayList<>();

        // --- Prepare Message with Image Content ---
        Map<String, Object> userMessage = new HashMap<>();
        userMessage.put("role", "user");

        List<Map<String, Object>> contentList = new ArrayList<>();
        // Part 1: Text
        Map<String, Object> textPart = new HashMap<>();
        textPart.put("type", "text");
        textPart.put("text", "What is in this image? If it\'s a nature scene, describe the most prominent colors.");
        contentList.add(textPart);

        // Part 2: Image (using a public URL)
        Map<String, Object> imageUrlPart = new HashMap<>();
        Map<String, String> imageUrlDetail = new HashMap<>();
        imageUrlDetail.put("url", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/1024px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg");
        imageUrlDetail.put("detail", "low"); // Can be "low", "high", or "auto"
        
        imageUrlPart.put("type", "image_url");
        imageUrlPart.put("image_url", imageUrlDetail);
        contentList.add(imageUrlPart);

        // Example for local image (Base64 encoded):
        // try {
        //     String localImagePath = "example.jpg"; // Replace with your image path
        //     String base64Image = encodeImageToBase64(localImagePath);
        //     Map<String, Object> imageBase64Part = new HashMap<>();
        //     Map<String, String> imageBase64Detail = new HashMap<>();
        //     imageBase64Detail.put("url", "data:image/jpeg;base64," + base64Image);
        //     imageBase64Detail.put("detail", "auto");

        //     imageBase64Part.put("type", "image_url");
        //     imageBase64Part.put("image_url", imageBase64Detail);
        //     contentList.add(imageBase64Part);
        //     System.out.println("Added local image as Base64.");
        // } catch (IOException e) {
        //     System.err.println("Error processing local image for Base64: " + e.getMessage());
        //     // Potentially skip adding this part or handle error
        // }

        userMessage.put("content", contentList);
        messages.add(userMessage);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("max_tokens", 300);
        requestBodyMap.put("temperature", 0.5);

        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName); // e.g., "gpt-4-vision-preview"
        } else {
            System.out.println("No vision model specified in .env, using placeholder 'gpt-4-vision-preview'. Ensure your endpoint supports this.");
            requestBodyMap.put("model", "gpt-4-vision-preview");
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
                .timeout(Duration.ofSeconds(90)) // Longer timeout for vision models
                .build();

        System.out.println("Sending image input request to: " + request.uri());
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            System.out.println("--- API Response --- ");
            System.out.println("Status Code: " + response.statusCode());
            System.out.println("Body: " + response.body());
            System.out.println("------------------------------------");

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                try {
                    Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                    List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                    if (choices != null && !choices.isEmpty()) {
                        Map<String, Object> firstChoice = choices.get(0);
                        Map<String, String> responseMessage = (Map<String, String>) firstChoice.get("message");
                        if (responseMessage != null) {
                            System.out.println("Assistant Message: " + responseMessage.get("content"));
                        }
                    }
                } catch (Exception e) {
                    System.err.println("Error parsing JSON response: " + e.getMessage());
                }
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
        }

        System.out.println("HTTP client image input example complete.");
    }
} 