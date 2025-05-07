package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Scanner;

public class HttpClientMultiImage {

    public static void main(String[] args) {
        ConfigLoader.loadEnv();
        String apiKey = ConfigLoader.getApiKey();
        String baseUrl = ConfigLoader.getBaseUrl();
        String model = ConfigLoader.getModelName();

        String imageUrl1 = "https://example.com/image1.jpg"; // Replace with actual image URL
        String imageUrl2 = "https://example.com/image2.png"; // Replace with actual image URL

        System.out.println("--- HTTP Client Multi-Image Input Example ---");
        System.out.println("Base URL: " + baseUrl);
        System.out.println("Model: " + model);
        System.out.println("Image URL 1: " + imageUrl1);
        System.out.println("Image URL 2: " + imageUrl2);

        try {
            URL url = new URL(baseUrl + "/chat/completions");
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("Authorization", "Bearer " + apiKey);
            connection.setDoOutput(true);

            ObjectMapper objectMapper = new ObjectMapper();
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("model", model);
            requestBody.put("max_tokens", 300);
            requestBody.put("temperature", 0.7);

            ArrayNode messages = objectMapper.createArrayNode();
            ObjectNode userMessage = objectMapper.createObjectNode();
            userMessage.put("role", "user");

            // Constructing multi-part content for the user message
            ArrayNode contentArray = objectMapper.createArrayNode();

            ObjectNode textPart = objectMapper.createObjectNode();
            textPart.put("type", "text");
            textPart.put("text", "What are in these images? Describe the first one, then the second.");
            contentArray.add(textPart);

            ObjectNode imagePart1 = objectMapper.createObjectNode();
            imagePart1.put("type", "image_url");
            ObjectNode imageUrlObject1 = objectMapper.createObjectNode();
            imageUrlObject1.put("url", imageUrl1);
            imagePart1.set("image_url", imageUrlObject1);
            contentArray.add(imagePart1);

            ObjectNode imagePart2 = objectMapper.createObjectNode();
            imagePart2.put("type", "image_url");
            ObjectNode imageUrlObject2 = objectMapper.createObjectNode();
            imageUrlObject2.put("url", imageUrl2);
            imagePart2.set("image_url", imageUrlObject2);
            contentArray.add(imagePart2);

            userMessage.set("content", contentArray);
            messages.add(userMessage);
            requestBody.set("messages", messages);

            String jsonInputString = objectMapper.writeValueAsString(requestBody);
            System.out.println("\nRequest Body:\n" + jsonInputString);

            System.out.println("\nSending request to API...");
            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonInputString.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            int responseCode = connection.getResponseCode();
            System.out.println("Response Code: " + responseCode);

            StringBuilder response = new StringBuilder();
            if (responseCode == HttpURLConnection.HTTP_OK) {
                try (Scanner scanner = new Scanner(connection.getInputStream(), StandardCharsets.UTF_8.name())) {
                    while (scanner.hasNextLine()) {
                        response.append(scanner.nextLine().trim());
                    }
                }
            } else {
                try (Scanner scanner = new Scanner(connection.getErrorStream(), StandardCharsets.UTF_8.name())) {
                    while (scanner.hasNextLine()) {
                        response.append(scanner.nextLine().trim());
                    }
                }
            }
            connection.disconnect();

            System.out.println("Response Body:\n" + response.toString());

            // Pretty print JSON response
            Object parsedJson = objectMapper.readValue(response.toString(), Object.class);
            System.out.println("Pretty Printed Response Body:\n" + objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(parsedJson));

            System.out.println("\nMulti-image input example via HTTP completed.");

        } catch (Exception e) {
            System.err.println("An error occurred: " + e.getMessage());
            e.printStackTrace();
        }
    }
} 