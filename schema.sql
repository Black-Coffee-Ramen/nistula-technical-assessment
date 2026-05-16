-- Nistula Unified Guest Messaging Platform
-- PostgreSQL Schema Design
-- Goal: Production-style relational design, maintainability, and AI lifecycle tracking.

-- --------------------------------------------------
-- 1. ENUMS & EXTENSIONS
-- --------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Unified sources across the platform
CREATE TYPE message_source AS ENUM (
    'whatsapp',
    'booking_com',
    'airbnb',
    'instagram',
    'direct'
);

-- Query types for AI classification
CREATE TYPE query_type AS ENUM (
    'pre_sales_availability',
    'pre_sales_pricing',
    'post_sales_checkin',
    'special_request',
    'complaint',
    'general_enquiry'
);

-- Direction of the message
CREATE TYPE message_direction AS ENUM (
    'inbound',
    'outbound'
);

-- The final action taken by the system or human
CREATE TYPE action_state AS ENUM (
    'auto_sent',
    'agent_review',
    'escalated'
);

-- Type of message sender
CREATE TYPE sender_type AS ENUM (
    'guest',
    'system_ai',
    'agent'
);

-- Status of a reservation
CREATE TYPE reservation_status AS ENUM (
    'pending',
    'confirmed',
    'cancelled',
    'completed'
);

-- --------------------------------------------------
-- 2. CORE TABLES
-- --------------------------------------------------

-- GUESTS: Centralized guest profile.
-- We decouple the "Person" from their "Channel Identity" to support multi-channel resolution.
CREATE TABLE guests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    primary_email TEXT UNIQUE,
    primary_phone TEXT UNIQUE,
    internal_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GUEST_CHANNEL_IDENTITIES: Maps platform-specific IDs to a central guest.
-- Example: A phone number for WhatsApp, an encrypted ID for Airbnb.
CREATE TABLE guest_channel_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guest_id UUID NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
    source message_source NOT NULL,
    channel_user_id TEXT NOT NULL, -- The unique ID from the platform (e.g. "919876543210")
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source, channel_user_id)
);

-- RESERVATIONS: Linking bookings to guests.
CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guest_id UUID NOT NULL REFERENCES guests(id) ON DELETE RESTRICT,
    property_id TEXT NOT NULL, -- Logical ID (e.g. "villa-b1")
    booking_ref TEXT NOT NULL UNIQUE,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    total_guests INTEGER NOT NULL DEFAULT 1,
    status reservation_status NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CONVERSATIONS: Logical grouping of related messages.
-- Allows grouping pre-sales vs post-sales threads.
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guest_id UUID NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
    reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
    title TEXT, -- Optional, e.g. "Inquiry about Villa B1"
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MESSAGES: Unified table for all communication (Inbound & Outbound).
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    direction message_direction NOT NULL,
    sender_type sender_type NOT NULL,
    source message_source NOT NULL,
    
    -- Content
    content_raw TEXT NOT NULL, -- Original verbatim message
    content_normalized TEXT,   -- Cleaned/translated message for AI processing
    
    -- AI Metadata (Populated ONLY for inbound messages)
    msg_query_type query_type,
    confidence_score NUMERIC(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Lifecycle Tracking
    is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE, -- True if the reply was drafted by Claude
    was_agent_edited BOOLEAN NOT NULL DEFAULT FALSE, -- True if a human modified the AI draft
    action_taken action_state,                       -- auto_sent, agent_review, or escalated
    agent_id UUID,                                   -- Future FK reference to internal_users(id)
    
    -- External Reference (from platform webhook if available)
    external_msg_id TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate processing of the same platform message
    UNIQUE(source, external_msg_id)
);

-- --------------------------------------------------
-- 3. INDEXING
-- --------------------------------------------------

-- Fast lookup for booking references
CREATE INDEX idx_reservations_booking_ref ON reservations(booking_ref);

-- Trace identity across platforms
CREATE INDEX idx_channel_identities_user_id ON guest_channel_identities(channel_user_id);

-- Conversation threading optimization
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Guest search performance
CREATE INDEX idx_guests_full_name ON guests(full_name);

-- --------------------------------------------------
-- 4. ARCHITECTURE EXPLANATION
-- --------------------------------------------------
/*
DESIGN RATIONALE:
1. Separation of Identity: The 'guests' vs 'guest_channel_identities' design is built for future scale. 
   It acknowledges that guests are nomadic across platforms. By indexing 'channel_user_id', we can 
   quickly resolve a returning guest even if they use a different app.

2. Unified Messaging: Storing inbound and outbound messages in one table ('messages') with a 'direction' 
   column ensures that conversation ordering is always consistent and simplifies reporting on AI performance.

3. AI Lineage: The fields 'is_ai_generated', 'was_agent_edited', and 'action_taken' provide a complete 
   audit trail. This allows Nistula to calculate "Automation Rate" vs "Human Correction Rate" effectively.
   
4. Operational Flexibility: The 'reservation_id' in 'conversations' is optional (Nullable). This supports 
   Pre-Sales queries (where no booking exists yet) and Post-Sales issues (where we link to a stay).
*/

-- --------------------------------------------------
-- 5. HARDEST DESIGN DECISION
-- --------------------------------------------------
/*
HARDEST DESIGN DECISION: Cross-Channel Identity Resolution vs. Data Integrity.
The most difficult decision was modeling the guest identity given the weak identifiers provided by 
channel webhooks (often just a name and source). A naive design would simply store guest data in the 
'messages' table, leading to massive duplication and a broken "Guest History" view.

I chose to implement a dedicated 'guest_channel_identities' table as a buffer. This allows us to 
gracefully handle the current limitation (treating every new name-source pair as a new guest) while 
providing a clear architectural path for "Guest Merging" logic. In the future, once we detect a 
matching email or phone number in a message body or reservation, we can simply point multiple 
channel identities to a single 'guest_id', instantly unifying their entire communication history 
without refactoring the schema.
*/
