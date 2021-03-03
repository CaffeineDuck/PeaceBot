-- upgrade --
CREATE TABLE IF NOT EXISTS "guilds" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "prefix" VARCHAR(10) NOT NULL
);
COMMENT ON COLUMN "guilds"."id" IS 'Discord ID of the guild';
COMMENT ON COLUMN "guilds"."prefix" IS 'Custom prefix of the guild';
COMMENT ON TABLE "guilds" IS 'Represents a discord guild''s settings';
CREATE TABLE IF NOT EXISTS "users" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY
);
COMMENT ON COLUMN "users"."id" IS 'Discord ID of the user';
COMMENT ON TABLE "users" IS 'Represents all users';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
