from discord.ext import commands
from services.tasks.acl_manager import ACLManager
from services.logging import logger

acl_manager = ACLManager()

async def add_user(ctx, username: str, ports: str = "22/tcp"):
    """Add a user to the ACL."""
    try:
        logger.info(f"Adding user {username} with ports {ports}")
        result = acl_manager.add_user_to_acl(username, ports.split(","))
        await ctx.send(f"✅ {result}")
    except Exception as e:
        logger.error(f"Error adding user {username}: {str(e)}")
        await ctx.send(f"❌ Error adding user: {str(e)}")

async def remove_user(ctx, username: str):
    """Remove a user from the ACL."""
    try:
        logger.info(f"Removing user {username} from ACL")
        result = acl_manager.remove_user_from_acl(username)
        await ctx.send(f"✅ {result}")
    except Exception as e:
        logger.error(f"Error removing user {username}: {str(e)}")
        await ctx.send(f"❌ Error removing user: {str(e)}")

# TODO: gotta add granularity here as well
async def list_acl_roles(ctx):
    """List all user roles in the ACL."""
    try:
        logger.info("Listing ACL roles")
        users = acl_manager.list_acl_roles()
        if users:
            acl_list = "\n".join(users)
            await ctx.send(f"🔑 Users with SSH access:\n{acl_list}")
        else:
            logger.warning("No ACL roles found")
            await ctx.send("No users found.")
    except Exception as e:
        logger.error(f"Error listing roles: {str(e)}")
        await ctx.send(f"❌ Error listing roles: {str(e)}")

async def list_tailnet_users(ctx):
    """List all users in tailnet."""
    try:
        logger.info("Listing tailnet users")
        users = acl_manager.list_tailnet_users()
        if users:
            tailnet_list = "\n".join(users)
            await ctx.send(f"🔑 Users in tailnet:\n{tailnet_list}")
        else:
            logger.warning("No tailnet users found")
            await ctx.send("No users found.")
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        await ctx.send(f"❌ Error listing users: {str(e)}")

async def update_user(ctx, username: str, ports: str):
    """Update the ports for an existing user."""
    try:
        logger.info(f"Updating user {username} with ports {ports}")
        result = acl_manager.update_user_acl(username, ports.split(","))
        await ctx.send(f"✅ {result}")
    except Exception as e:
        logger.error(f"Error updating user {username}: {str(e)}")
        await ctx.send(f"❌ Error updating user: {str(e)}")
