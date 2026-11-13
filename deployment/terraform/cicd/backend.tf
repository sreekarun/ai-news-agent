terraform {
  backend "gcs" {
    bucket = "adk-chatbot-prod-terraform-state"
    prefix = "ai-news-agent/prod"
  }
}
