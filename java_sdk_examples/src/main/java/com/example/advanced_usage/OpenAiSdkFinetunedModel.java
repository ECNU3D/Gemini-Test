package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatCompletionChoice;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.service.OpenAiService;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkFinetunedModel {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        // The MODEL_NAME env var should be set to your fine-tuned model ID for this example
        // e.g., "ft:gpt-3.5-turbo-0613:your-org:custom-suffix:idstring"
        String finetunedModelId = ConfigLoader.getModelName(); 

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        if (finetunedModelId == null || finetunedModelId.trim().isEmpty() || !finetunedModelId.startsWith("ft:")) {
            System.err.println("ERROR: A fine-tuned model ID is not configured or is invalid.");
            System.err.println("Please set the MODEL_NAME environment variable to your fine-tuned model ID.");
            System.err.println("Example: ft:gpt-3.5-turbo-0613:your-org:custom-suffix:idstring");
            System.err.println("If you don\'t have a fine-tuned model, this example won\'t work as intended.");
            // For demonstration, we can fallback to a base model, but it defeats the purpose.
            // finetunedModelId = "gpt-3.5-turbo"; // Fallback for basic execution
            // System.out.println("Warning: Using fallback base model: " + finetunedModelId);
             return; 
        }

        System.out.println("--- TheoKanning/openai-java SDK Using Fine-tuned Model --- ");
        System.out.println("Attempting to use fine-tuned model: " + finetunedModelId);

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30)).newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
                System.out.println("Using custom API base URL: " + apiBaseUrl);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
                System.out.println("Using default OpenAI API base URL.");
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<ChatMessage> messages = new ArrayList<>();
        // Craft a prompt that is suitable for your fine-tuned model's specialization
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "What is the key characteristic of Project Alpha? Tell me based on its specialized training."));

        ChatCompletionRequest request = ChatCompletionRequest.builder()
                .model(finetunedModelId) // Specify the fine-tuned model ID here
                .messages(messages)
                .temperature(0.7)
                .n(1)
                .build();

        System.out.println("Sending request to fine-tuned model...");
        System.out.println("Model: " + request.getModel());
        System.out.println("Messages: " + request.getMessages().stream().map(m -> m.getRole() + ": " + m.getContent()).collect(Collectors.joining("\n")) );
        System.out.println("------------------------------------");

        try {
            List<ChatCompletionChoice> choices = service.createChatCompletion(request).getChoices();

            System.out.println("--- API Response --- ");
            if (choices != null && !choices.isEmpty()) {
                ChatMessage assistantMessage = choices.get(0).getMessage();
                System.out.println("Assistant Message: " + assistantMessage.getContent());
            } else {
                 System.out.println("No choices returned in the response.");
            }
            System.out.println("------------------------------------");

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
            try {
                System.err.println("Error Body: " + (e.response() != null && e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
             System.err.println("Ensure your fine-tuned model ID is correct and accessible with your API key.");
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        service.shutdownExecutor();
        System.out.println("SDK Fine-tuned Model example complete.");
    }
} 