package com.example.basic_inference;

import com.example.utils.ConfigLoader;
import com.openai.client.OpenAIClient; // Check actual import path after adding dependency
import com.openai.client.models.ChatCompletionRequest;
import com.openai.client.models.ChatCompletionResponse;
import com.openai.client.models.ChatMessage;
import com.openai.client.models.ChatRole;
import com.openai.client.models.OpenAIError;
import com.openai.client.models.OpenAIException;

import java.util.ArrayList;
import java.util.List;

public class OpenAiSdkNormal {

    public static void main(String[] args) {
        // Load configuration
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String model = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- OpenAI Java SDK Normal Chat Completion --- ");

        // --- Initialize OpenAI Client ---
        // The SDK might require specific setup for custom base URLs
        OpenAIClient client = new OpenAIClient.Builder()
                .setApiKey(apiKey)
                .setBaseUrl(apiBaseUrl) // Method name might differ
                // Add other configurations like timeout if needed
                .build();

        // --- Prepare API Request --- 
        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatRole.USER, "What is the capital of France?"));

        ChatCompletionRequest request = new ChatCompletionRequest.Builder()
                .setModel(model) // Required by SDK, even if backend doesn't use it
                .setMessages(messages)
                .setTemperature(0.7)
                // Add other parameters like maxTokens if needed
                .build();

        System.out.println("Sending request...");
        System.out.println("Model: " + (model != null ? model : "Default"));
        System.out.println("Messages: " + messages);
        System.out.println("------------------------------------");

        try {
            // --- Send Request & Get Response --- 
            ChatCompletionResponse response = client.getChatCompletions(request); // Method name might differ

            System.out.println("--- Full API Response --- ");
            // The SDK likely provides a way to serialize the response object
            // For now, just printing key parts
            System.out.println("ID: " + response.getId());
            System.out.println("Model: " + response.getModel());
            System.out.println("Created: " + response.getCreated());
            System.out.println("Usage: " + response.getUsage()); // May need null check
            
            if (response.getChoices() != null && !response.getChoices().isEmpty()) {
                 ChatMessage assistantMessage = response.getChoices().get(0).getMessage();
                 System.out.println("Assistant Message: " + assistantMessage.getContent());
            } else {
                 System.out.println("No choices returned in the response.");
            }

            System.out.println("------------------------------------");

        } catch (OpenAIException e) {
            System.err.println("API Error occurred: " + e.getMessage());
            OpenAIError error = e.getError();
            if (error != null) {
                System.err.println("Error Type: " + error.getType());
                System.err.println("Error Code: " + error.getCode());
                System.err.println("Error Param: " + error.getParam());
                System.err.println("Error Details: " + error.getMessage());
            }
            e.printStackTrace(); // Print stack trace for more details
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("Basic SDK example complete.");
    }
} 