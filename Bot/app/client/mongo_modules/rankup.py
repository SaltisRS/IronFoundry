from loguru import logger

from ..modules.mongo import MongoClient

client = MongoClient()
connected = False

async def client_connect() -> None:
    global connected
    if not connected:
        try:
            await client.connect()
            await client.set_database("IronFoundry")
            connected = True
        except Exception as e:
            connected = False
            logger.error(f"Error connecting to MongoDB: {e}")
            
            
async def get_user(user_id: int) -> None | dict:
    await client_connect()
    try:
        users = await client.get_collection("Users")
        user = await client.get_document(users, {"_id": user_id})
        return {"rank": user["rank"], "rsn": user["rsn"], "alts": user["alts"]}
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None
    finally:
        await client.close()
        global connected
        connected = False
    
async def get_ranks() -> None | dict:
    await client_connect()
    try:
        rank_collection = await client.get_collection("Ranking System")
        ranks = await client.get_many(rank_collection, {})
        return ranks
    except Exception as e:
        logger.error(f"Error getting ranks: {e}")
        return None
    finally:
        await client.close()
        global connected
        connected = False
    
async def update_user(user_id: int, update: dict) -> None:
    await client_connect()
    try:
        users = await client.get_collection("Users")
        await client.update_document(users, {"_id": user_id}, {"$set": update})
    except Exception as e:
        logger.error(f"Error updating user: {e}")
    finally:
        await client.close()
        global connected
        connected = False
        
async def start_rankup(user_id: int):
    await client_connect()
    rank_dict = {}
    try:
        user = await get_user(user_id)
        accounts = user.get("rsn")
        alts = user.get("alts")
        if alts:
            for alt in alts:
                accounts.append(alt.get("rsn"))
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
    try:
        ranks = await get_ranks()
        rank_dict.update(ranks)
    except Exception as e:
        logger.error(f"Error fetching ranks: {e}")
    
    rankup_doc = {
        "_id": user_id,
        "accounts": accounts,
        "ranks": rank_dict,
        "selected_rank": None
    }
    try:
        await client.insert_document("Active Rankups", rankup_doc)
    except Exception as e:
        logger.error(f"Error inserting rankup {e}")
    finally:
        await client.close()
        global connected
        connected = False
        
async def get_active_rankup(user_id: int) -> None | dict:
    await client_connect()
    try:
        active_rankup = await client.get_document("Active Rankups", {"_id": user_id})
        return active_rankup
    except Exception as e:
        logger.error(f"Error getting active rankup: {e}")
        return None
    finally:
        await client.close()
        global connected
        connected = False

async def update_active_rankup(user_id: int, rank: str):
    await client_connect()
    try:
        await client.update_document("Active Rankups", {"_id": user_id}, {"$set": {"selected_rank": rank}})
    except Exception as e:
        logger.error(f"Error updating active rankup: {e}")
    finally:
        await client.close()
        global connected
        connected = False

async def close_active_rankup(user_id: int):
    await client_connect()
    try:
        user_curr = await get_user(user_id)
        user_new = await client.get_document("Active Rankups", {"_id": user_id})
        user_curr["rank"] = user_new["selected_rank"]
        await update_user(user_id, user_curr)
        await client.get_collection("Active Rankups").delete_one({"_id": user_id})
    except Exception as e:
        logger.error(f"Error closing rankup: {e}")
    finally:
        await client.close()
        global connected
        connected = False
        
