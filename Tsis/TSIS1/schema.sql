BEGIN;

CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO groups(name)
VALUES ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(20),              -- legacy primary phone from Practice 7/8
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS email VARCHAR(100);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS birthday DATE;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS group_id INTEGER;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

UPDATE contacts
SET group_id = (SELECT id FROM groups WHERE name = 'Other')
WHERE group_id IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_contacts_group'
    ) THEN
        ALTER TABLE contacts
        ADD CONSTRAINT fk_contacts_group
        FOREIGN KEY (group_id) REFERENCES groups(id);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) NOT NULL DEFAULT 'mobile'
               CHECK (type IN ('home', 'work', 'mobile'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_phones_contact_phone ON phones(contact_id, phone);
CREATE INDEX IF NOT EXISTS idx_contacts_group_id ON contacts(group_id);
CREATE INDEX IF NOT EXISTS idx_contacts_name_lower ON contacts(LOWER(name));
CREATE INDEX IF NOT EXISTS idx_contacts_email_lower ON contacts(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_phones_phone ON phones(phone);

-- Migrate old contacts.phone values into the normalized phones table.
INSERT INTO phones(contact_id, phone, type)
SELECT c.id, c.phone, 'mobile'
FROM contacts c
WHERE c.phone IS NOT NULL AND BTRIM(c.phone) <> ''
ON CONFLICT (contact_id, phone) DO NOTHING;

COMMIT;
