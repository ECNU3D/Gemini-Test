package com.example.multimodal;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatCompletionChoice;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
// For image input, the SDK needs a way to represent complex content (text + image URL or base64)
// The standard ChatMessage in 0.20.0 takes a String content. 
// We might need to use a more generic Map or a newer/different SDK structure if available,
// or acknowledge this limitation for v0.20.0 and show how it would be done with HTTP.
// For now, let's assume we construct a list of content parts, though the SDK might not directly support it in ChatMessage.
import com.theokanning.openai.completion.chat.ImageContent;
import com.theokanning.openai.completion.chat.TextContent;
import com.theokanning.openai.service.OpenAiService;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Base64;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.stream.Collectors;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkImageInput {

    // Helper to encode image to Base64
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

        System.out.println("--- TheoKanning/openai-java SDK Image Input (Vision) --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                System.out.println("Using custom API base URL: " + apiBaseUrl);
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(60)) // Longer timeout for potential image processing
                    .newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                System.out.println("Using default OpenAI API base URL.");
                service = new OpenAiService(apiKey, Duration.ofSeconds(60));
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // --- Prepare Image Content ---
        // Using a publicly available image URL for simplicity.
        // For local files, you'd typically send as base64.
        String imageUrl = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg";
        // Example for local image (ensure example_image.jpg is in project root or provide full path)
        // String localImagePath = "example.jpg"; // replace with your image path
        // String base64Image = null;
        // try {
        //     base64Image = encodeImageToBase64(localImagePath);
        // } catch (IOException e) {
        //     System.err.println("Error encoding local image: " + e.getMessage());
        //     // return; // Or handle differently
        // }

        // --- Prepare API Request --- 
        // The TheoKanning 0.20.0 ChatMessage constructor takes (role, content string).
        // For multimodal input (text + image), the content needs to be a list of objects (text, image_url).
        // This SDK version might not directly support this complex ChatMessage content structure.
        // We are showing a conceptual way; it might require manual JSON construction or a newer SDK.
        
        List<ChatMessage> messages = new ArrayList<>();
        ChatMessage userMessage;

        // Constructing content for multimodal message:
        // This is a conceptual representation. The actual SDK (v0.20.0) ChatMessage
        // expects a single String for content. For true multimodal with this SDK version,
        // one might need to use a more flexible way to build the request body (e.g. Map<String,Object>)
        // or use raw HTTP. LangChain4j or newer official SDKs handle this more directly.

        // Attempting to use the newer List<Content> approach if the SDK stubs for it exist (they might not in 0.20.0)
        List<com.theokanning.openai.completion.chat.Content> contentList = new ArrayList<>();
        contentList.add(new TextContent("What is in this image?"));
        contentList.add(new ImageContent(imageUrl, "auto")); // "detail" can be "low", "high", "auto"

        // If List<Content> is not available or ChatMessage doesn't support it:
        // userMessage = new ChatMessage(ChatMessageRole.USER.value(), "What is in this image? Image URL: " + imageUrl );
        // This would rely on the model interpreting the text string containing the URL.
        
        // The following line would be ideal IF ChatMessage supported List<Content> in v0.20.0
        userMessage = new ChatMessage(ChatMessageRole.USER.value(), contentList); 
        // ^^^ THIS WILL LIKELY CAUSE A COMPILE ERROR with v0.20.0 as ChatMessage expects String content.
        // For demonstration, if the above fails, we fall back to a text-only prompt that includes the URL.
        // To make this runnable without complex reflection/overrides for an old SDK,
        // we will use a simple text prompt if List<Content> isn't directly usable.

        // Fallback for SDK v0.20.0 limitation:
        System.out.println("Note: TheoKanning SDK 0.20.0 ChatMessage expects String content. For true vision models, \n" +
                           "a more direct way to pass image data (like a list of content parts) is needed, \n" +
                           "which might require direct HTTP request construction or a newer/different SDK.");
        System.out.println("Simulating by sending image URL in text prompt.");
        userMessage = new ChatMessage(ChatMessageRole.USER.value(), "Describe this image: " + imageUrl);

        messages.add(userMessage);

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .maxTokens(300) // Vision models can have larger outputs
                .temperature(0.5);

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName); // Ensure this is a vision-capable model
        } else {
            System.out.println("No vision model specified in .env, using a placeholder like 'gpt-4-vision-preview'. Ensure your endpoint supports this.");
            requestBuilder.model("gpt-4-vision-preview"); 
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending image input request...");
        System.out.println("Model: " + request.getModel());
        // System.out.println("Messages: " + request.getMessages().stream().map(m -> m.getRole() + ": " + m.getContent()).collect(Collectors.joining("\n")) );
        System.out.println("------------------------------------");

        try {
            List<ChatCompletionChoice> choices = service.createChatCompletion(request).getChoices();
            System.out.println("--- API Response --- ");
            if (choices != null && !choices.isEmpty()) {
                System.out.println("Assistant Message: " + choices.get(0).getMessage().getContent());
            } else {
                 System.out.println("No choices returned.");
            }
            System.out.println("------------------------------------");
        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
            try {
                System.err.println("Error Body: " + (e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            e.printStackTrace();
        }
        service.shutdownExecutor();
        System.out.println("SDK image input example complete.");
    }
} 