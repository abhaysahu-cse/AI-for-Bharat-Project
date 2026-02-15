# AI for Bharat - Technical Design Document

## 1. High-Level Architecture Overview

### 1.1 System Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Mobile App    │    │   Admin Panel   │
│   (React/Next)  │    │   (React Native)│    │   (React)       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     API Gateway           │
                    │   (Kong/AWS API Gateway)  │
                    │   - Auth & Rate Limiting  │
                    │   - Request Routing       │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   AI Orchestration        │
                    │   (Node.js/Python)        │
                    │   - Prompt Engine         │
                    │   - Workflow Management   │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│   Model Layer     │   │  Vector DB &      │   │  Analytics &      │
│   - OpenAI GPT-4  │   │  Knowledge Store  │   │  Feedback Loop    │
│   - Oracle GenAI  │   │  - Pinecone       │   │  - ClickHouse     │
│   - Llama-3       │   │  - PostgreSQL     │   │  - Redis          │
│   - DALL-E        │   │  - S3/MinIO       │   │  - Kafka          │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   Storage & CDN           │
                    │   - AWS S3/CloudFlare     │
                    │   - Media Processing      │
                    │   - Asset Management      │
                    └───────────────────────────┘
```

### 1.2 Component Rationale

#### Frontend Layer
- **Web Application**: React/Next.js for responsive, SEO-friendly interface
- **Mobile App**: React Native for cross-platform mobile experience
- **Admin Panel**: Separate React application for content moderation and analytics

#### API Gateway
- **Kong/AWS API Gateway**: Centralized request routing, authentication, and rate limiting
- **Load Balancing**: Distribute traffic across multiple backend instances
- **Security**: SSL termination, DDoS protection, and request validation

#### AI Orchestration Layer
- **Prompt Engine**: Template management and prompt optimization
- **Workflow Management**: Coordinate complex multi-step AI operations
- **Model Selection**: Route requests to appropriate AI models based on task type

#### Model Layer
- **Primary Models**: OpenAI GPT-4, Oracle GenAI for high-quality generation
- **Fallback Models**: Llama-3, Mistral for cost optimization and redundancy
- **Specialized Models**: DALL-E for images, specialized models for code/technical content

#### Vector DB & Knowledge Store
- **Pinecone**: Vector similarity search for RAG implementation
- **PostgreSQL**: Structured data storage for user profiles, content metadata
- **S3/MinIO**: Object storage for media files and large documents

#### Analytics & Feedback Loop
- **ClickHouse**: High-performance analytics database for real-time metrics
- **Redis**: Caching layer for frequently accessed data
- **Kafka**: Event streaming for real-time analytics and model feedback

## 2. Module Definitions

### 2.1 Frontend Module

#### UI Patterns
```typescript
// Component Structure
src/
├── components/
│   ├── common/          // Reusable UI components
│   ├── content/         // Content creation components
│   ├── analytics/       // Analytics dashboards
│   └── collaboration/   // Team collaboration features
├── pages/
│   ├── create/          // Content creation flows
│   ├── schedule/        // Publishing scheduler
│   └── analytics/       // Performance analytics
└── hooks/
    ├── useContent.ts    // Content management
    ├── useAnalytics.ts  // Analytics data
    └── useAuth.ts       // Authentication
```

#### Caching Strategy
- **Service Worker**: Cache static assets and API responses
- **React Query**: Server state management with intelligent caching
- **Local Storage**: User preferences and draft content
- **IndexedDB**: Large media files and offline content

#### Offline-First Considerations
- **Progressive Web App**: Service worker for offline functionality
- **Optimistic Updates**: Update UI immediately, sync when online
- **Conflict Resolution**: Handle conflicts when multiple devices edit same content
- **Sync Queue**: Queue operations for execution when connection restored

### 2.2 API & Gateway Module

#### Core Endpoints
- **Authentication**: `/auth/*` - User authentication and session management
- **Content**: `/api/v1/content/*` - Content CRUD operations
- **AI Services**: `/api/v1/ai/*` - AI-powered content generation
- **Analytics**: `/api/v1/analytics/*` - Performance metrics and insights
- **Admin**: `/api/v1/admin/*` - Administrative functions

#### Rate Limiting
```yaml
# Rate limiting configuration
rate_limits:
  free_tier:
    requests_per_minute: 10
    requests_per_hour: 100
    requests_per_day: 500
  paid_tier:
    requests_per_minute: 100
    requests_per_hour: 2000
    requests_per_day: 10000
  enterprise:
    requests_per_minute: 1000
    requests_per_hour: 50000
    requests_per_day: 500000
```

#### Authentication Flow
- **OAuth 2.0**: Google, Facebook, Microsoft integration
- **JWT Tokens**: Stateless authentication with refresh tokens
- **Role-Based Access**: Admin, Editor, Contributor, Viewer roles
- **API Keys**: For programmatic access and integrations

### 2.3 Prompt Engine Module

#### Template Management
```python
class PromptTemplate:
    def __init__(self, template_id: str, template: str, variables: List[str]):
        self.template_id = template_id
        self.template = template
        self.variables = variables
        self.version = "1.0"
    
    def render(self, context: Dict[str, Any]) -> str:
        return self.template.format(**context)
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        return all(var in context for var in self.variables)
```

#### Persona & Tone Control
- **Persona Profiles**: Creator, Publisher, Brand, Educator personas
- **Tone Modifiers**: Formal, casual, humorous, educational, promotional
- **Cultural Context**: Regional preferences and cultural adaptations
- **Brand Voice**: Consistent brand personality across content

#### Prompt Chaining Patterns
- **Sequential Chaining**: Output of one prompt feeds into next
- **Parallel Processing**: Multiple prompts executed simultaneously
- **Conditional Logic**: Dynamic prompt selection based on context
- **Feedback Loops**: Iterative refinement based on quality scores

#### Guardrails
- **Content Filters**: Explicit content, hate speech, misinformation detection
- **Cultural Sensitivity**: Regional and religious sensitivity checks
- **Brand Safety**: Ensure content aligns with brand guidelines
- **Legal Compliance**: Copyright and trademark violation prevention

### 2.4 Retrieval Layer Module

#### Embedding Pipeline
```python
class EmbeddingPipeline:
    def __init__(self, model_name: str = "text-embedding-ada-002"):
        self.model = OpenAIEmbeddings(model=model_name)
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    def process_document(self, document: str, metadata: Dict) -> List[Chunk]:
        chunks = self.chunk_document(document)
        embeddings = self.model.embed_documents(chunks)
        return [
            Chunk(text=chunk, embedding=emb, metadata=metadata)
            for chunk, emb in zip(chunks, embeddings)
        ]
```

#### Indexing Strategy
- **Hierarchical Indexing**: Topic → Subtopic → Document → Chunk
- **Metadata Indexing**: Language, source, date, license information
- **Semantic Clustering**: Group similar content for efficient retrieval
- **Update Mechanisms**: Incremental updates for new content

#### Document Chunking
- **Size Limits**: 1000 characters per chunk with 200 character overlap
- **Semantic Boundaries**: Respect paragraph and sentence boundaries
- **Context Preservation**: Maintain context across chunk boundaries
- **Metadata Inheritance**: Propagate document metadata to chunks

#### Freshness Policy
- **Time-Based Decay**: Reduce relevance score for older content
- **Update Frequency**: Daily updates for news, weekly for evergreen content
- **Version Control**: Track document versions and update embeddings
- **Expiration Rules**: Automatic removal of outdated content

### 2.5 Model Layer Module

#### Model Selection Strategy
```python
class ModelRouter:
    def __init__(self):
        self.models = {
            "text_generation": ["gpt-4", "oracle-genai", "llama-3"],
            "translation": ["gpt-4", "google-translate", "azure-translator"],
            "image_generation": ["dall-e-3", "stable-diffusion", "midjourney"],
            "code_generation": ["gpt-4", "starcoder", "codellama"]
        }
    
    def select_model(self, task_type: str, priority: str = "quality") -> str:
        available_models = self.models.get(task_type, [])
        if priority == "cost":
            return available_models[-1]  # Cheapest option
        elif priority == "speed":
            return available_models[1]   # Balanced option
        else:
            return available_models[0]   # Highest quality
```

#### Fallback Strategy
- **Primary → Secondary → Tertiary**: Graceful degradation across model tiers
- **Health Monitoring**: Real-time model availability and performance tracking
- **Circuit Breaker**: Automatic failover when models are unavailable
- **Cost Optimization**: Route to cheaper models when quality difference is minimal

#### Batching vs Streaming
- **Batch Processing**: Non-urgent requests processed in batches for cost efficiency
- **Streaming**: Real-time generation for interactive content creation
- **Hybrid Approach**: User preference and request type determine processing mode
- **Queue Management**: Priority queues for different request types

#### Response Post-Processing
- **Citation Injection**: Automatically add source citations to generated content
- **Quality Scoring**: Assess content quality and flag low-quality outputs
- **Format Standardization**: Ensure consistent output formatting
- **Safety Filtering**: Final safety check before returning content to user

### 2.6 Moderation & Copyright Module

#### Content Filters
```python
class ContentModerator:
    def __init__(self):
        self.explicit_filter = ExplicitContentFilter()
        self.hate_speech_filter = HateSpeechFilter()
        self.cultural_sensitivity_filter = CulturalSensitivityFilter()
    
    def moderate_content(self, content: str, language: str) -> ModerationResult:
        results = []
        results.append(self.explicit_filter.check(content))
        results.append(self.hate_speech_filter.check(content, language))
        results.append(self.cultural_sensitivity_filter.check(content, language))
        
        return ModerationResult.aggregate(results)
```

#### License Verification
- **Image License Checking**: Verify usage rights for generated and uploaded images
- **Text Source Attribution**: Track and attribute text sources appropriately
- **Copyright Database**: Maintain database of copyrighted content for comparison
- **Fair Use Assessment**: Automated fair use evaluation for referenced content

#### Watermarking
- **Digital Watermarks**: Embed invisible watermarks in generated images
- **Text Fingerprinting**: Create unique fingerprints for generated text content
- **Provenance Tracking**: Maintain chain of custody for all generated content
- **Attribution Metadata**: Embed attribution information in content metadata

### 2.7 Scheduler & Connector Module

#### Abstract Connector Interface
```python
class SocialMediaConnector(ABC):
    @abstractmethod
    def authenticate(self, credentials: Dict) -> bool:
        pass
    
    @abstractmethod
    def publish_post(self, content: ContentItem) -> PublishResult:
        pass
    
    @abstractmethod
    def schedule_post(self, content: ContentItem, schedule_time: datetime) -> str:
        pass
    
    @abstractmethod
    def get_analytics(self, post_id: str) -> AnalyticsData:
        pass
```

#### Platform-Specific Implementations
- **Instagram Connector**: Instagram Basic Display API integration
- **Facebook Connector**: Facebook Graph API for pages and groups
- **X (Twitter) Connector**: Twitter API v2 for posting and analytics
- **YouTube Connector**: YouTube Data API for video uploads and community posts
- **WhatsApp Connector**: WhatsApp Business API for status updates
- **Regional Platform Connectors**: ShareChat, Moj, Josh, Koo integrations

#### Scheduling Engine
- **Cron-Based Scheduling**: Reliable job scheduling with cron expressions
- **Time Zone Handling**: Proper time zone conversion for global users
- **Retry Logic**: Exponential backoff for failed publishing attempts
- **Bulk Operations**: Efficient handling of bulk scheduling requests

### 2.8 Analytics Engine Module

#### Event Tracking Schema
```python
class AnalyticsEvent:
    event_type: str          # "content_created", "post_published", "engagement"
    user_id: str            # User identifier
    content_id: str         # Content identifier
    platform: str           # Social media platform
    timestamp: datetime     # Event timestamp
    properties: Dict        # Event-specific properties
    session_id: str         # User session identifier
    device_info: Dict       # Device and browser information
```

#### Metrics Calculations
- **Engagement Rate**: (Likes + Comments + Shares) / Impressions
- **Cultural Resonance Score**: Weighted score based on regional engagement patterns
- **Content Quality Score**: Combination of user edits, approval rate, and engagement
- **Performance Trends**: Time-series analysis of content performance

#### Feedback Loop Integration
- **Model Performance Tracking**: Track model accuracy and user satisfaction
- **A/B Test Results**: Feed test results back into content generation algorithms
- **User Preference Learning**: Adapt content generation based on user behavior
- **Quality Improvement**: Continuous model fine-tuning based on user feedback

## 3. API Surface

### 3.1 Content Generation API

#### POST /api/v1/ai/create
Generate content variants based on input parameters.

**Request Schema:**
```json
{
  "prompt": "Create a Diwali greeting post for Instagram",
  "content_type": "social_post",
  "platform": "instagram",
  "language": "hindi",
  "tone": "festive",
  "variants": 3,
  "max_length": 280,
  "include_hashtags": true,
  "brand_guidelines": {
    "voice": "friendly",
    "avoid_topics": ["politics", "religion"]
  }
}
```

**Response Schema:**
```json
{
  "request_id": "req_123456789",
  "status": "success",
  "variants": [
    {
      "id": "var_001",
      "content": "दीवाली की हार्दिक शुभकामनाएं! 🪔✨ इस त्योहार में आपके जीवन में खुशियों की रोशनी आए। #Diwali2024 #FestivalOfLights #Celebration",
      "confidence_score": 0.92,
      "cultural_relevance": 0.89,
      "platform_optimization": {
        "character_count": 127,
        "hashtag_count": 3,
        "emoji_count": 2
      }
    }
  ],
  "sources": [
    {
      "url": "https://example.com/diwali-traditions",
      "title": "Diwali Celebration Guide",
      "relevance_score": 0.85
    }
  ],
  "processing_time_ms": 2340
}
```

### 3.2 Localization API

#### POST /api/v1/ai/localize
Translate and culturally adapt content for different regions.

**Request Schema:**
```json
{
  "content": "Happy New Year! Wishing you success and prosperity in the coming year.",
  "source_language": "english",
  "target_languages": ["hindi", "bengali", "tamil"],
  "cultural_adaptation": true,
  "preserve_formatting": true,
  "context": {
    "content_type": "greeting",
    "audience": "general",
    "formality": "casual"
  }
}
```

**Response Schema:**
```json
{
  "request_id": "loc_987654321",
  "status": "success",
  "translations": [
    {
      "language": "hindi",
      "content": "नव वर्ष की हार्दिक शुभकामनाएं! आने वाले साल में आपको सफलता और समृद्धि मिले।",
      "confidence_score": 0.94,
      "cultural_adaptations": [
        {
          "original": "Happy New Year",
          "adapted": "नव वर्ष की हार्दिक शुभकामनाएं",
          "reason": "More culturally appropriate greeting format"
        }
      ]
    }
  ],
  "human_review_recommended": false,
  "processing_time_ms": 1850
}
```

### 3.3 Platform Optimization API

#### POST /api/v1/ai/optimize
Optimize content for specific social media platforms.

**Request Schema:**
```json
{
  "content": "Long-form article about sustainable living practices and their impact on environment...",
  "target_platforms": ["instagram", "twitter", "facebook", "linkedin"],
  "optimization_goals": ["engagement", "reach", "conversions"],
  "include_media_suggestions": true
}
```

**Response Schema:**
```json
{
  "request_id": "opt_456789123",
  "status": "success",
  "optimized_content": [
    {
      "platform": "instagram",
      "format": "carousel_post",
      "content": {
        "slides": [
          {
            "text": "🌱 5 Simple Ways to Live Sustainably",
            "image_prompt": "Minimalist illustration of green living practices"
          }
        ]
      },
      "hashtags": ["#SustainableLiving", "#EcoFriendly", "#GreenLife"],
      "best_posting_time": "2024-01-25T18:30:00Z"
    }
  ],
  "performance_prediction": {
    "estimated_reach": 2500,
    "estimated_engagement_rate": 0.045
  }
}
```

### 3.4 Scheduling API

#### POST /api/v1/schedule
Schedule content for publishing across multiple platforms.

**Request Schema:**
```json
{
  "content_id": "content_789123456",
  "schedule": [
    {
      "platform": "instagram",
      "publish_time": "2024-01-26T09:00:00Z",
      "timezone": "Asia/Kolkata"
    },
    {
      "platform": "facebook",
      "publish_time": "2024-01-26T10:00:00Z",
      "timezone": "Asia/Kolkata"
    }
  ],
  "approval_required": true,
  "auto_optimize_timing": true
}
```

**Response Schema:**
```json
{
  "schedule_id": "sched_321654987",
  "status": "scheduled",
  "scheduled_posts": [
    {
      "platform": "instagram",
      "scheduled_time": "2024-01-26T09:00:00Z",
      "status": "pending_approval",
      "post_id": "post_ig_001"
    }
  ],
  "approval_url": "https://app.aiforabharat.com/approve/sched_321654987",
  "estimated_reach": 5000
}
```

### 3.5 Analytics API

#### GET /api/v1/analytics
Retrieve performance metrics and insights.

**Query Parameters:**
- `content_id`: Specific content ID (optional)
- `date_range`: Date range for analytics (required)
- `platforms`: Comma-separated list of platforms (optional)
- `metrics`: Specific metrics to retrieve (optional)

**Response Schema:**
```json
{
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "summary": {
    "total_posts": 45,
    "total_impressions": 125000,
    "total_engagement": 8750,
    "average_engagement_rate": 0.07,
    "top_performing_platform": "instagram"
  },
  "platform_breakdown": [
    {
      "platform": "instagram",
      "posts": 20,
      "impressions": 75000,
      "engagement": 5250,
      "engagement_rate": 0.07,
      "top_content_type": "carousel"
    }
  ],
  "cultural_resonance": {
    "overall_score": 0.82,
    "regional_breakdown": [
      {
        "region": "north_india",
        "score": 0.85,
        "engagement_lift": 0.12
      }
    ]
  }
}
```

### 3.6 Asset Management API

#### GET /api/v1/assets/:id
Retrieve media assets and metadata.

**Response Schema:**
```json
{
  "asset_id": "asset_123456789",
  "type": "image",
  "url": "https://cdn.aiforabharat.com/assets/asset_123456789.jpg",
  "metadata": {
    "filename": "diwali_greeting.jpg",
    "size": 245760,
    "dimensions": {
      "width": 1080,
      "height": 1080
    },
    "format": "JPEG",
    "created_at": "2024-01-25T10:30:00Z"
  },
  "usage_rights": {
    "license": "CC-BY-4.0",
    "attribution_required": true,
    "commercial_use": true
  },
  "optimization_variants": [
    {
      "platform": "instagram_story",
      "url": "https://cdn.aiforabharat.com/assets/asset_123456789_ig_story.jpg",
      "dimensions": {"width": 1080, "height": 1920}
    }
  ]
}
```

### 3.7 Feedback API

#### POST /api/v1/feedback
Submit user feedback for content quality improvement.

**Request Schema:**
```json
{
  "content_id": "content_789123456",
  "feedback_type": "quality_rating",
  "rating": 4,
  "comments": "Good content but could use more cultural context",
  "specific_issues": [
    {
      "type": "cultural_accuracy",
      "severity": "minor",
      "description": "Festival date reference could be more specific"
    }
  ],
  "user_edits": [
    {
      "original": "Happy Diwali everyone!",
      "edited": "दीवाली की हार्दिक शुभकामनाएं सभी को!",
      "edit_type": "language_preference"
    }
  ]
}
```

**Response Schema:**
```json
{
  "feedback_id": "fb_456789123",
  "status": "received",
  "impact": {
    "model_training": true,
    "immediate_improvements": [
      "Cultural context database updated",
      "Language preference model adjusted"
    ]
  },
  "reward_points": 10,
  "thank_you_message": "Thank you for helping us improve AI for Bharat!"
}
```

## 4. Data Models & Schemas

### 4.1 User Profile Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255),
    role user_role_enum DEFAULT 'creator',
    
    -- Language preferences
    primary_language VARCHAR(10) DEFAULT 'english',
    secondary_languages TEXT[], -- Array of language codes
    
    -- Regional settings
    country VARCHAR(2) DEFAULT 'IN',
    state VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    
    -- Subscription and credits
    subscription_tier subscription_tier_enum DEFAULT 'free',
    credits_remaining INTEGER DEFAULT 100,
    credits_used_today INTEGER DEFAULT 0,
    
    -- Platform connections
    connected_platforms JSONB DEFAULT '{}',
    
    -- Preferences
    content_preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);

-- Enums
CREATE TYPE user_role_enum AS ENUM ('admin', 'editor', 'creator', 'contributor', 'viewer');
CREATE TYPE subscription_tier_enum AS ENUM ('free', 'basic', 'pro', 'enterprise');
```

### 4.2 Content Draft Schema

```sql
CREATE TABLE content_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Content details
    title VARCHAR(500),
    content_type content_type_enum NOT NULL,
    primary_language VARCHAR(10) NOT NULL,
    
    -- Content versions
    current_version INTEGER DEFAULT 1,
    versions JSONB NOT NULL DEFAULT '[]',
    
    -- Status and workflow
    draft_status draft_status_enum DEFAULT 'draft',
    approval_status approval_status_enum DEFAULT 'pending',
    assigned_reviewer_id UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    category VARCHAR(100),
    
    -- Source citations
    source_citations JSONB DEFAULT '[]',
    
    -- Platform optimization
    platform_variants JSONB DEFAULT '{}',
    
    -- Scheduling
    scheduled_publish_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Analytics
    performance_metrics JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enums
CREATE TYPE content_type_enum AS ENUM ('social_post', 'article', 'image_caption', 'video_script', 'email', 'ad_copy');
CREATE TYPE draft_status_enum AS ENUM ('draft', 'review', 'approved', 'published', 'archived');
CREATE TYPE approval_status_enum AS ENUM ('pending', 'approved', 'rejected', 'needs_revision');
```

### 4.3 Embedding & Document Index Schema

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Document information
    document_id UUID NOT NULL,
    document_title VARCHAR(500),
    document_url TEXT,
    
    -- Chunk details
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    
    -- Embedding
    embedding VECTOR(1536), -- OpenAI ada-002 embedding dimension
    
    -- Metadata
    language VARCHAR(10),
    content_type VARCHAR(50),
    source_type source_type_enum,
    
    -- Licensing and attribution
    license VARCHAR(100),
    attribution_required BOOLEAN DEFAULT false,
    copyright_holder VARCHAR(255),
    
    -- Freshness and quality
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified_at TIMESTAMP WITH TIME ZONE,
    quality_score DECIMAL(3,2),
    
    -- Indexing
    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index)
);

-- Vector similarity index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Text search index
CREATE INDEX ON document_chunks USING gin (to_tsvector('english', chunk_text));

-- Enums
CREATE TYPE source_type_enum AS ENUM ('web_crawl', 'user_upload', 'api_import', 'manual_entry', 'news_feed');
```

### 4.4 Analytics Event Schema

```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event identification
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50),
    
    -- User and content context
    user_id UUID REFERENCES users(id),
    content_id UUID REFERENCES content_drafts(id),
    session_id VARCHAR(100),
    
    -- Platform context
    platform VARCHAR(50),
    platform_post_id VARCHAR(255),
    
    -- Event data
    event_properties JSONB DEFAULT '{}',
    metric_values JSONB DEFAULT '{}',
    
    -- Device and location
    device_info JSONB DEFAULT '{}',
    user_agent TEXT,
    ip_address INET,
    country VARCHAR(2),
    region VARCHAR(100),
    
    -- Timestamp
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for analytics queries
CREATE INDEX idx_analytics_events_user_time ON analytics_events (user_id, event_timestamp DESC);
CREATE INDEX idx_analytics_events_content_time ON analytics_events (content_id, event_timestamp DESC);
CREATE INDEX idx_analytics_events_type_time ON analytics_events (event_type, event_timestamp DESC);
CREATE INDEX idx_analytics_events_platform_time ON analytics_events (platform, event_timestamp DESC);
```

## 5. Prompt-Engine Design & Patterns

### 5.1 Prompt Templates

#### Template 1: Tone Adaptation
```python
TONE_ADAPT_TEMPLATE = """
System: You are an expert content adapter specializing in Indian cultural contexts and regional communication styles.

User: Adapt the following content to match the specified tone and cultural context:

Original Content: {original_content}
Target Tone: {target_tone}
Target Audience: {target_audience}
Cultural Context: {cultural_context}
Language: {language}

Requirements:
- Maintain the core message while adapting tone
- Include culturally relevant references when appropriate
- Ensure language is natural and engaging for the target audience
- Preserve any factual information accurately
Assistant: Provide the adapted content that resonates with the target audience while maintaining authenticity.
"""

# Example usage
tone_adapt_example = {
    "original_content": "Our new product launch is exciting and innovative",
    "target_tone": "festive",
    "target_audience": "young professionals in Mumbai",
    "cultural_context": "Diwali season",
    "language": "hindi"
}
```

#### Template 2: Short Post Variants
```python
SHORT_POST_VARIANTS_TEMPLATE = """
System: You are a social media content specialist creating engaging short-form content for Indian audiences.

User: Create {variant_count} different versions of a social media post based on the following:

Topic: {topic}
Platform: {platform}
Language: {language}
Tone: {tone}
Character Limit: {char_limit}
Include Hashtags: {include_hashtags}
Target Audience: {target_audience}

Requirements:
- Each variant should have a different approach or angle
- Optimize for the specified platform's best practices
- Include relevant emojis and hashtags where appropriate
- Ensure cultural relevance for Indian audiences
- Maintain engagement-focused writing style
Assistant: Provide {variant_count} distinct, engaging social media post variants.
"""

# Example usage
short_post_example = {
    "variant_count": 3,
    "topic": "sustainable living tips",
    "platform": "instagram",
    "language": "english",
    "tone": "educational",
    "char_limit": 2200,
    "include_hashtags": True,
    "target_audience": "environmentally conscious millennials"
}
```

#### Template 3: Image Captioning
```python
IMAGE_CAPTIONING_TEMPLATE = """
System: You are an expert at creating detailed, culturally-aware image descriptions and captions for Indian content.

User: Create a compelling caption for an image with the following details:

Image Description: {image_description}
Content Context: {content_context}
Platform: {platform}
Language: {language}
Tone: {tone}
Brand Voice: {brand_voice}

Requirements:
- Create an engaging caption that complements the image
- Include relevant cultural context if applicable
- Optimize for the specified platform's audience
- Include call-to-action if appropriate
- Suggest relevant hashtags
- Ensure accessibility with descriptive elements
Assistant: Provide an engaging, culturally-relevant caption with suggested hashtags.
"""
```

#### Template 4: Cultural Tone Shift
```python
CULTURAL_TONE_SHIFT_TEMPLATE = """
System: You are a cultural adaptation specialist with deep knowledge of Indian regional cultures and communication styles.

User: Adapt the following content for different regional Indian audiences:

Original Content: {original_content}
Source Region: {source_region}
Target Regions: {target_regions}
Content Type: {content_type}
Preserve Core Message: {preserve_message}

For each target region, consider:
- Regional communication preferences
- Cultural references and festivals
- Local language influences on expression
- Appropriate formality levels
- Regional business or social customs

Requirements:
- Maintain the original intent and key information
- Adapt cultural references to be locally relevant
- Adjust tone to match regional communication styles
- Ensure respectful and appropriate cultural representation
Assistant: Provide culturally-adapted versions for each target region with explanations of key adaptations made.
"""
```

#### Template 5: Long-Form Summarization
```python
SUMMARIZE_LONG_FORM_TEMPLATE = """
System: You are an expert content summarizer specializing in creating engaging, digestible summaries for Indian audiences.

User: Create a summary of the following content:

Original Content: {original_content}
Summary Type: {summary_type}  # bullet_points, paragraph, social_media, executive_summary
Target Length: {target_length}
Language: {language}
Audience: {target_audience}
Key Points to Emphasize: {key_points}

Requirements:
- Capture the most important information accurately
- Maintain the original tone and intent
- Make it engaging and easy to understand
- Include relevant cultural context if present
- Ensure factual accuracy and proper attribution
- Optimize for the specified audience and format
Assistant: Provide a well-structured summary that captures the essential information in the requested format.
"""
```

#### Template 6: Video Storyboard Generation
```python
GENERATE_STORYBOARD_TEMPLATE = """
System: You are a video content strategist specializing in short-form video content for Indian social media platforms.

User: Create a detailed storyboard for a short video based on:

Video Topic: {video_topic}
Duration: {duration_seconds} seconds
Platform: {platform}
Target Audience: {target_audience}
Language: {language}
Style: {video_style}  # educational, entertaining, promotional, storytelling
Key Message: {key_message}

Requirements:
- Break down into specific scenes with timing
- Include visual descriptions for each scene
- Suggest text overlays, captions, or voiceover
- Recommend background music or sound effects
- Include cultural elements relevant to Indian audiences
- Optimize for vertical video format if platform requires
- Suggest engaging hooks for the first 3 seconds
Assistant: Provide a detailed scene-by-scene storyboard with timing, visuals, and audio recommendations.
"""
```

### 5.2 Chain-of-Thought Avoidance

The prompt engine avoids explicit chain-of-thought reasoning to maintain efficiency and reduce token usage:

```python
# Instead of: "Let me think step by step..."
# Use structured prompts with clear role definitions:

STRUCTURED_PROMPT_PATTERN = """
System: {role_definition}

User: {task_description}
{input_data}

Requirements:
{specific_requirements}