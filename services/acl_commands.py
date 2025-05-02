from discord.ext import commands
from services.tasks.acl_manager import ACLManager
from services.logging import logger
from services.logging.audit import log_command_audit
import discord

acl_manager = ACLManager()

async def add_user(ctx, username: str, ports: str = "22/tcp", ttl_hours: int = None):
    """
    Add a user to the ACL.
    
    Parameters:
        username: The username to add
        ports: Comma-separated list of ports (default: 22/tcp)
        ttl_hours: Optional time-to-live in hours for temporary access
    """
    try:
        # Log command to audit log
        log_command_audit(ctx.author.name, "adduser", username, ports, ttl_hours)
        
        logger.info(f"Adding user {username} with ports {ports}")
        if ttl_hours is not None:
            logger.info(f"Setting temporary access with TTL of {ttl_hours} hours")
            await ctx.send(f"⏱️ Adding {username} with temporary access ({ttl_hours} hours)")
            result = acl_manager.add_user_to_acl(username, ports.split(","), ttl_hours)
        else:
            result = acl_manager.add_user_to_acl(username, ports.split(","))
        
        await ctx.send(f"✅ {result}")
    except Exception as e:
        logger.error(f"Error adding user {username}: {str(e)}")
        await ctx.send(f"❌ Error adding user: {str(e)}")

async def remove_user(ctx, username: str):
    """Remove a user from the ACL."""
    try:
        # Log command to audit log
        log_command_audit(ctx.author.name, "removeuser", username)
        
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
        # Log command to audit log
        log_command_audit(ctx.author.name, "updateuser", username, ports)
        
        logger.info(f"Updating user {username} with ports {ports}")
        result = acl_manager.update_user_acl(username, ports.split(","))
        await ctx.send(f"✅ {result}")
    except Exception as e:
        logger.error(f"Error updating user {username}: {str(e)}")
        await ctx.send(f"❌ Error updating user: {str(e)}")

async def list_acl_details(ctx):
    """List ACL details including expiration times for temporary access."""
    try:
        logger.info("Listing detailed ACL information")
        
        # Get the raw ACL data
        acl_data = acl_manager.get_acls()
        if not acl_data or "acls" not in acl_data or not acl_data["acls"]:
            await ctx.send("No ACL entries found.")
            return
        
        # Create an embed to display the information
        embed = discord.Embed(
            title="🔑 ACL Details",
            description=f"Current access control entries ({len(acl_data['acls'])} total)",
            color=discord.Color.blue()
        )
        
        # Process each ACL entry
        for i, entry in enumerate(acl_data["acls"]):
            users = ", ".join(entry.get("users", []))
            ports = ", ".join(entry.get("ports", []))
            
            # Determine if this is a temporary entry with expiration
            is_temporary = False
            expiry_info = ""
            comment = entry.get("comment", "")
            
            if "// expires_at:" in comment:
                is_temporary = True
                try:
                    # Extract and format the expiration time
                    expires_str = comment.split("// expires_at:")[1].strip()
                    expiry_info = f"⏱️ Expires: {expires_str}"
                except Exception:
                    expiry_info = "⏱️ Has expiration (format error)"
            
            # Create the field content
            content = f"**Ports:** {ports}"
            if expiry_info:
                content += f"\n{expiry_info}"
            
            # Add a field for this entry
            title = f"{'🕒 ' if is_temporary else ''}Users: {users}"
            embed.add_field(name=title, value=content, inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Error listing ACL details: {str(e)}")
        await ctx.send(f"❌ Error listing ACL details: {str(e)}")
