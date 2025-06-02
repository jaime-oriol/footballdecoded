// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      // Añadir el ID del usuario a la sesión
      if (session.user && token.sub) {
        // @ts-ignore - NextAuth types don't include id by default
        session.user.id = token.sub
      }
      return session
    },
    async jwt({ token, account, profile }) {
      // Persistir el OAuth account
      if (account) {
        token.accessToken = account.access_token
      }
      return token
    },
  },
})

export { handler as GET, handler as POST }
