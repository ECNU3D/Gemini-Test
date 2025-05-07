package com.example.utils;

import io.github.cdimascio.dotenv.Dotenv;
import io.github.cdimascio.dotenv.DotenvException;

public class ConfigLoader {

    private static Dotenv dotenv;

    static {
        try {
            // Load .env file from the project root (assuming execution from java_sdk_examples)
            dotenv = Dotenv.configure().directory("../").ignoreIfMissing().load(); // Go up one level
            if (dotenv == null) {
                 // Fallback: Try loading from current directory if run differently
                 dotenv = Dotenv.configure().ignoreIfMissing().load();
            }
             if (dotenv == null) {
                System.err.println("Warning: .env file not found. Trying environment variables.");
                // Initialize with system environment variables as fallback
                dotenv = Dotenv.configure().systemProperties().ignoreIfMalformed().load();
             }

        } catch (DotenvException e) {
            System.err.println("Could not load .env file: " + e.getMessage());
            // Initialize with system environment variables as fallback
             dotenv = Dotenv.configure().systemProperties().ignoreIfMalformed().load();
        }
    }

    public static String getApiKey() {
        String key = dotenv.get("OPENAI_API_KEY");
        if (key == null || key.isEmpty()) {
            System.err.println("Error: OPENAI_API_KEY not found in .env file or system environment.");
            // Return a dummy key or throw an exception based on desired behavior
            return "DUMMY_API_KEY";
        }
        return key;
    }

    public static String getApiBaseUrl() {
        return dotenv.get("OPENAI_API_BASE", "http://localhost:8000/v1"); // Default if not set
    }

    public static String getModelName() {
        // Return null if empty or not set, as some endpoints don't require it
        String modelName = dotenv.get("MODEL_NAME");
        return (modelName == null || modelName.trim().isEmpty()) ? null : modelName.trim();
    }

     // Prevent instantiation
    private ConfigLoader() {}
}
