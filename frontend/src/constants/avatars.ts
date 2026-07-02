/** Preset avatar paths — PNGs live in frontend/public/avatars/ */

export const USER_AVATARS = Array.from({ length: 20 }, (_, i) =>
  `/avatars/users/u${i + 1}.png`,
);

export const ADMIN_AVATARS = Array.from({ length: 5 }, (_, i) =>
  `/avatars/admins/a${i + 1}.png`,
);

export function getRandomUserAvatar(): string {
  const idx = Math.floor(Math.random() * USER_AVATARS.length);
  return USER_AVATARS[idx];
}

export function isValidUserAvatar(url: string): boolean {
  return USER_AVATARS.includes(url);
}

export function isValidAdminAvatar(url: string): boolean {
  return ADMIN_AVATARS.includes(url);
}
