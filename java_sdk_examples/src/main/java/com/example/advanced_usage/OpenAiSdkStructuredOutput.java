package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
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
import static com.theokanning.openai.service.OpenAiService.*;

// Define the POJO for the desired structured output
class UserProfile {
    private final String name;
    private final int age;
    private final String city;
    private final List<String> interests;

    @JsonCreator
    public UserProfile(@JsonProperty("name") String name, 
                       @JsonProperty("age") int age, 
                       @JsonProperty("city") String city,
                       @JsonProperty("interests") List<String> interests) {
        this.name = name;
        this.age = age;
        this.city = city;
        this.interests = interests;
    }

    // Getters (important for Jackson deserialization if fields are private)
    public String getName() { return name; }
    public int getAge() { return age; }
    public String getCity() { return city; }
    public List<String> getInterests() { return interests; }

    @Override
    public String toString() {
        return "UserProfile{" +
               "name='" + name + '\'' +
               ", age=" + age +
               ", city='" + city + '\'' +
               ", interests=" + interests +
               '}';
    }
}

public class OpenAiSdkStructuredOutput {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Structured Output Example --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30)).newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                com.theokanning.openai.client.OpenAiApi openAiApi = retrofit.create(com.theokanning.openai.client.OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatMessageRole.SYSTEM.value(), 
            "You are an assistant that provides user profile information strictly in JSON format. " +
            "The JSON object must conform to the following structure: " +
            "{\"name\": \"string\", \"age\": integer, \"city\": \"string\", \"interests\": [\"string\"]}. " + 
            "Do not add any extra text or explanations outside of the JSON object."));
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), 
            "Generate a fictional user profile for a person named Alex who is 30 years old, lives in New York, and is interested in hiking and coding."));

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .temperature(0.5); // Lower temperature for more predictable structured output
                // Note: TheoKanning SDK 0.20.0 does not have a direct `responseFormat` or `toolChoice` for arbitrary JSON schemas outside of functions.
                // We rely on strong prompting for JSON output.

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            System.out.println("No model specified, using 'gpt-3.5-turbo-1106' (or newer) as it handles JSON well.");
            requestBuilder.model("gpt-3.5-turbo-1106"); 
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending request for structured output (via prompt)...");
        System.out.println("Model: " + request.getModel());
        System.out.println("------------------------------------");

        try {
            ChatMessage assistantMessage = service.createChatCompletion(request).getChoices().get(0).getMessage();
            String rawResponseContent = assistantMessage.getContent();
            System.out.println("Raw Assistant Message Content:\n" + rawResponseContent);
            System.out.println("------------------------------------");

            // Attempt to deserialize into the POJO
            try {
                UserProfile userProfile = objectMapper.readValue(rawResponseContent, UserProfile.class);
                System.out.println("Successfully deserialized into UserProfile object:");
                System.out.println(userProfile);
            } catch (JsonProcessingException e) {
                System.err.println("Failed to deserialize response into UserProfile: " + e.getMessage());
                System.err.println("Model output was not valid JSON conforming to the UserProfile structure, or the prompt was not followed precisely.");
            }

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
             try {
                System.err.println("Error Body: " + (e.response() != null && e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        service.shutdownExecutor();
        System.out.println("SDK Structured Output example complete.");
    }
} 