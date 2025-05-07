package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.client.OpenAiApi;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.service.OpenAiService;
import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import retrofit2.adapter.rxjava2.RxJava2CallAdapterFactory;
import retrofit2.converter.jackson.JacksonConverterFactory;

import java.time.Duration;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;

public class OpenAiSdkMultiImage {

    public static void main(String[] args) {
        ConfigLoader.loadEnv();
        String apiKey = ConfigLoader.getApiKey();
        String baseUrl = ConfigLoader.getBaseUrl();
        String model = ConfigLoader.getModelName();

        // The TheoKanning SDK (0.20.0) ChatMessage content is a String.
        // For multimodal inputs with multiple images, we typically need to send a list of content parts (text, image_url).
        // Since the SDK doesn't directly support this structure for ChatMessage,
        // we will include multiple image URLs in the text prompt itself as a common workaround.
        // This relies on the model's ability to understand and process these URLs from the text.

        String imageUrl1 = "https://example.com/image1.jpg"; // Replace with actual image URL
        String imageUrl2 = "https://example.com/image2.png"; // Replace with actual image URL
        String userPrompt = "What are in these images? Image 1: " + imageUrl1 + " Image 2: " + imageUrl2 +
                            "\nDescribe the content of the first image and then the second one.";

        System.out.println("--- OpenAI SDK Multi-Image Input Example ---");
        System.out.println("Base URL: " + baseUrl);
        System.out.println("Model: " + model);
        System.out.println("User Prompt with Image URLs: " + userPrompt);

        try {
            // Custom OkHttpClient and Retrofit setup to use the custom base URL
            OkHttpClient client = new OkHttpClient.Builder()
                    .connectTimeout(Duration.ofSeconds(30))
                    .readTimeout(Duration.ofSeconds(120)) // Increased timeout for potentially larger responses
                    .build();

            Retrofit retrofit = new Retrofit.Builder()
                    .baseUrl(baseUrl + "/") // Base URL must end in /
                    .client(client)
                    .addConverterFactory(JacksonConverterFactory.create())
                    .addCallAdapterFactory(RxJava2CallAdapterFactory.create())
                    .build();

            OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
            OpenAiService service = new OpenAiService(apiKey, openAiApi);


            ChatMessage userMessage = new ChatMessage(
                    ChatMessageRole.USER.value(),
                    userPrompt
            );

            ChatCompletionRequest chatCompletionRequest = ChatCompletionRequest.builder()
                    .model(model)
                    .messages(Collections.singletonList(userMessage))
                    .maxTokens(300)
                    .temperature(0.7)
                    .n(1)
                    .build();

            System.out.println("\nSending request to API...");
            service.createChatCompletion(chatCompletionRequest).getChoices().forEach(choice -> {
                System.out.println("Response: " + choice.getMessage().getContent());
            });

            System.out.println("\nMulti-image input example completed.");

        } catch (Exception e) {
            System.err.println("An error occurred: " + e.getMessage());
            e.printStackTrace();
        }
    }
} 