package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
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

// POJO definition (can be in its own file or nested for simplicity here)
class UserProfileHttp {
    private final String name;
    private final int age;
    private final String city;
    private final List<String> interests;
    private final String occupation;

    @JsonCreator
    public UserProfileHttp(@JsonProperty("name") String name, 
                           @JsonProperty("age") int age, 
                           @JsonProperty("city") String city,
                           @JsonProperty("interests") List<String> interests,
                           @JsonProperty("occupation") String occupation) {
        this.name = name;
        this.age = age;
        this.city = city;
        this.interests = interests;
        this.occupation = occupation;
    }

    // Getters
    public String getName() { return name; }
    public int getAge() { return age; }
    public String getCity() { return city; }
    public List<String> getInterests() { return interests; }
    public String getOccupation() { return occupation; }

    @Override
    public String toString() {
        return "UserProfileHttp{" +
               "name='" + name + '\'' +
               ", age=" + age +
               ", city='" + city + '\'' +
               ", interests=" + interests +
               ", occupation='" + occupation + '\'' +
               '}';
    }
}

public class HttpClientStructuredOutput {
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

        System.out.println("--- Java HTTP Client Structured Output Example --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        List<Map<String, Object>> messages = new ArrayList<>();
        Map<String, Object> systemMessage = new HashMap<>();
        systemMessage.put("role", "system");
        systemMessage.put("content", 
            "You are an assistant that provides user profile information strictly in JSON format. " +
            "The JSON object must conform to the following structure: " +
            "{\"name\": \"string\", \"age\": integer, \"city\": \"string\", \"interests\": [\"string\"], \"occupation\": \"string\"}. " +
            "Ensure the output is a single, valid JSON object without any additional explanations or markdown.");
        messages.add(systemMessage);
        
        Map<String, Object> userMessage = new HashMap<>();
        userMessage.put("role", "user");
        userMessage.put("content", "Generate a fictional user profile for Sarah, 42, from London, interested in photography and travel, working as a software engineer.");
        messages.add(userMessage);

        Map<String, Object> requestBodyMap = new HashMap<>();
        requestBodyMap.put("messages", messages);
        requestBodyMap.put("temperature", 0.3); // Low temperature for structured output
        
        // Enforce JSON output mode if the API supports it
        Map<String, String> responseFormat = new HashMap<>();
        responseFormat.put("type", "json_object");
        requestBodyMap.put("response_format", responseFormat);

        if (modelName != null && !modelName.isEmpty()) {
            requestBodyMap.put("model", modelName);
        } else {
            System.out.println("No model specified, using 'gpt-3.5-turbo-1106' or newer for JSON mode.");
            requestBodyMap.put("model", "gpt-3.5-turbo-1106");
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

        System.out.println("Sending request for structured output (HTTP Client with response_format)...");
        System.out.println("Request Body: " + requestBodyJson);
        System.out.println("------------------------------------");

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            System.out.println("Status Code: " + response.statusCode());
            String responseBody = response.body();
            System.out.println("Raw Response Body:\n" + responseBody);
            System.out.println("------------------------------------");

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                // In JSON mode, the main content of the message should be the JSON string
                Map<String, Object> responseMap = objectMapper.readValue(responseBody, Map.class);
                List<Map<String, Object>> choices = (List<Map<String, Object>>) responseMap.get("choices");
                if (choices != null && !choices.isEmpty()) {
                    Map<String, Object> firstChoice = choices.get(0);
                    Map<String, Object> messageFromAssistant = (Map<String, Object>) firstChoice.get("message");
                    if (messageFromAssistant != null && messageFromAssistant.get("content") instanceof String) {
                        String jsonContentString = (String) messageFromAssistant.get("content");
                        System.out.println("Extracted JSON content string:\n" + jsonContentString);
                        try {
                            UserProfileHttp userProfile = objectMapper.readValue(jsonContentString, UserProfileHttp.class);
                            System.out.println("Successfully deserialized into UserProfileHttp object:");
                            System.out.println(userProfile);
                        } catch (JsonProcessingException e) {
                            System.err.println("Failed to deserialize JSON content string into UserProfileHttp: " + e.getMessage());
                        }
                    } else {
                        System.err.println("Assistant message content is not a string or is missing.");
                    }
                } else {
                    System.err.println("No choices found in the response.");
                }
            } else {
                System.err.println("Request failed. Response body might contain error details.");
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request or processing response: " + e.getMessage());
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("HTTP Client Structured Output example complete.");
    }
} 