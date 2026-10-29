import torch 
import clip
from PIL import Image
import requests as req
import cv2
import uuid
from .embeddingResult import EmbeddingResult, EmbeddingsResults

class ClipEmbedder:

    def __init__(self, model_name:str="ViT-B/32", device:str|None=None):
        self.device = device or "cuda" if torch.cuda.is_available() else "cpu"
       
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        

    def embed_images(self, urls: list[str])->list[EmbeddingsResults]: 
        imageEmbeddings = [ EmbeddingsResults(uuid.uuid4(), self.encode_image_url(url).embedding) for url in urls]
        return imageEmbeddings

    def embed_videos(self, urls: list[str])->list[EmbeddingsResults]:
        # Store each sampled frame in the same visual vector collection as images.
        frame_embeddings = []
        for url in urls:
            frames = self.encode_video_url(url).frame_embeddings
            frame_embeddings.extend(
                EmbeddingsResults(uuid.uuid4(), frame_embedding)
                for frame_embedding in frames
            )
        return frame_embeddings
    
    def encode_video_url(self, video_url:str)-> EmbeddingResult:
        
            frames = self.extract_frames(video_url=video_url)
            frame_embeddings = self.encode_images(frames)

            video_embedding = frame_embeddings.mean(dim=0)
            video_embedding = (video_embedding / video_embedding.norm())


            return EmbeddingResult(embedding=video_embedding, frame_embeddings= frame_embeddings)
                
            

    # Processes a single image
    def encode_image_url(self, url:str, description:str|None = None)->EmbeddingResult:
        
        response = req.get(url, stream=True)
        response.raise_for_status()

        image = Image.open(response.raw)

        embedding = self.encode_image(image);
        text_embedding = self.encode_text(description) if description is not None else None

        return EmbeddingResult(embedding, text_embedding)

    
    def encode_image(self, image:Image.Image)->torch.Tensor:
        image = image.convert("RGB")
        processed = self.preprocess(image)
        processed = processed.unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model.encode_image(processed)

        return self._normalize(embedding).cpu()
    
    def encode_images(self, images: list[Image.Image]):
            processed = torch.stack([
                self.preprocess(image) for image in images
            ]).to(self.device)
    
            with torch.no_grad():
                embeddings = self.model.encode_image(processed)
            
            return self._normalize(embeddings).cpu()

    
    def encode_text(self, description):
        text = clip.tokenize([description]).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_text(text)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu()



    # Process video
    def extract_frames(video_url:str, max_frames=12)-> list[Image.Image]:
        cap = cv2.VideoCapture(video_url)

        if not cap.isOpened():
            raise RuntimeError("Error: Could not open video stream or file")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        if fps <= 0 or total_frames <= 0:
            cap.release()
            raise RuntimeError("Could not determine video properties")

        duration = total_frames / fps
        frame_count = min(max_frames, max(1, int(duration)))

        indices = [
            int(i * (total_frames - 1)/ max(1, frame_count - 1))
            for i in range(frame_count)
        ]


        frames:list[Image.Image] = []
        for index in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)

            ret, frame = cap.read()
            
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(frame))
            
        
        cap.release()
        
        return frames


    @staticmethod
    def _normalize(embeddings):
        return embeddings/embeddings.norm(dim=-1, keepdim=True)


