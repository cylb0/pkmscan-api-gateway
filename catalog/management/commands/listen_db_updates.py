from django.core.management.base import BaseCommand
from shared.aws import QueueAlias, aws_client, start_sqs_worker
from shared.messaging import DBUpdateMessage, CardImageProcessedPayload, ImageProcessingStatus, DBUpdateType
import logging
import sys
from catalog.models import LocalizedCard

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        
        logger.info("Starting SQS DB_UPDATES consumer...")

        def handle_db_updates(msg: dict):
            logger.info(f"Received message: {msg}")
            event: DBUpdateMessage = DBUpdateMessage.model_validate_json(msg["Body"])

            if event.event_type == DBUpdateType.CARD_IMAGE_PROCESSED:
                self._process_card_image_update(event.payload)
            else:
                logger.warning(f"Unknown event type received: {event.event_type}")

        start_sqs_worker(
            queue_alias=QueueAlias.DB_UPDATES,
            message_handler=handle_db_updates,
            client=aws_client
        )

    def _process_card_image_update(self, payload: CardImageProcessedPayload):
        "Updates a card state in database"
        card_id = payload.id
        status = payload.status
        
        logger.info(f"Processing DB update for card {card_id} with status {status.value}")

        try:
            card = LocalizedCard.objects.get(id=card_id)

            if status == ImageProcessingStatus.SUCCESS:
                if not payload.master_image_path:
                    logger.error(f"Received {status.value} status for card {card_id} but 'master_image_path' is missing or empty.")
                    return
                
                card.image_status = status.value
                card.master_image_path = payload.master_image_path
                card.save()
                logger.info(f"Successfully updated card {card_id} image status to {status.value}")
            
            elif status == ImageProcessingStatus.FAILED:
                error_msg = payload.error_message or "Unknown error occured during processing."

                card.image_status = status.value
                card.image_error_message = payload.error_message
                card.save()
                logger.warning(f"Card {card_id} processing failed. Error logged: {error_msg}")
        except LocalizedCard.DoesNotExist:
            logger.error(f"Card {card_id} not found in database. Unable to apply update.")
        except Exception as e:
            logger.error(f"Database error while updating card {card_id}: {e}")