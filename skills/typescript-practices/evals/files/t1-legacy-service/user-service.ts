export enum Role {
  Admin = "admin",
  Editor = "editor",
  Viewer = "viewer",
}

export interface User {
  id: string;
  name: string;
  role: Role;
}

export default class UserService {
  private cache: any = {};

  async fetchUser(id: string): Promise<User> {
    const res = await fetch(`/api/users/${id}`);
    const body = (await res.json()) as any;
    const user = body.user as unknown as User;
    this.cache[id] = user;
    return user;
  }

  firstAdmin(users: User[]): string {
    // @ts-ignore
    return users.find((u) => u.role === Role.Admin)!.name;
  }

  describe(role: Role): string {
    switch (role) {
      case Role.Admin:
        return "can do everything";
      case Role.Editor:
        return "can edit";
      default:
        return "can read";
    }
  }
}
