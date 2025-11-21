

# **Product Requirements Document: SAM 3 Labeller — Next-Generation Concept-Driven Annotation Platform Powered by Meta SAM 3**

## **1\. Strategic Context and Executive Summary**

### **1.1 The Paradigm Shift in Computer Vision**

The domain of computer vision data annotation is currently undergoing a fundamental transformation, migrating from a geometric, pixel-centric paradigm to a semantic, concept-driven workflow. For over a decade, the industry standard for annotation involved human laborers manually drawing bounding boxes and polygons—a process characterized by high latency, significant cost, and inherent subjectivity. The release of Meta’s Segment Anything Model 3 (SAM 3\) on November 19, 2025 1, necessitates a complete re-architecture of annotation tooling. Unlike its predecessors, SAM 1 and SAM 2, which primarily relied on spatial prompts such as points and boxes, SAM 3 introduces the capability of **Promptable Concept Segmentation (PCS)**.3 This architectural leap allows for the exhaustive segmentation of open-vocabulary concepts—for example, distinguishing a "yellow school bus" from the broader category of "bus"—across images and videos without the prerequisite of fixed ontologies.

This document outlines the product requirements for **SAM 3 Labeller**, an enterprise-grade web application designed natively around the SAM 3 architecture. SAM 3 Labeller aims to displace legacy tools such as CVAT, Label Studio, and primitive SAM 2 integrations by leveraging SAM 3’s unified encoder to reduce annotation time by approximately 36% for positive concept prompts and up to 500% (5x) for negative prompts.5 The platform is engineered to handle the specific computational demands of SAM 3, including its 848 million parameter architecture 4 and its linear inference cost scaling in video environments.5

### **1.2 Market Problem and Opportunity**

Current annotation platforms suffer from three structural bottlenecks that SAM 3 is uniquely positioned to resolve:

1. **Ontology Rigidity:** Traditional tools require a pre-defined schema before annotation begins. If a user discovers a new edge case (e.g., "occluded pedestrian with umbrella"), the schema must be updated and the job restarted. SAM 3’s open-vocabulary nature allows for dynamic ontology discovery.6  
2. **Video Tracking Drift:** Managing identity switches and occlusions in long-form video remains the most labor-intensive aspect of computer vision. While SAM 2 introduced memory tracking, it often requires frame-by-frame manual correction. SAM 3’s "masklet" architecture offers higher temporal consistency but requires a specialized UI to manage the memory bank’s propagation.7  
3. **Hardware-Software Latency Gap:** foundational models like SAM 3 require high-end GPUs (H100/H200) to achieve real-time inference of 30ms per image for 100+ objects.9 Running these models via standard APIs in a browser environment often introduces latency that degrades the user experience. SAM 3 Labeller addresses this via a hybrid architecture utilizing server-side H200 clusters for heavy lifting and client-side WebGPU-accelerated distilled models for interaction.10

### **1.3 Product Vision**

SAM 3 Labeller is defined as a "Text-First" annotation platform. The primary user interaction shifts from "drawing" to "verifying." Users define concepts via natural language, the system generates "presence tokens" and segmentation masklets, and the human-in-the-loop (HITL) refines the output only where confidence scores dip below a distinct threshold. This shift moves the economic value of the human annotator from motor skills (mouse precision) to semantic judgment (concept verification).

---

## **2\. Technical Architecture and Model Integration**

### **2.1 Core Model Backbone: SAM 3**

The heart of SAM 3 Labeller is the deep integration of Meta’s SAM 3\. Unlike wrapper applications that merely send API calls, SAM 3 Labeller’s backend is structured to utilize the specific components of the SAM 3 architecture.

#### **2.1.1 The Perception Encoder and DETR Detector**

SAM 3 utilizes a shared vision encoder known as the Meta Perception Encoder, which feeds into a DETR (DEtection TRansformer) based detector.5 This detector is conditioned on three distinct input types: text prompts, geometric prompts, and image exemplars. The platform must expose interfaces for all three:

* **Text Encoder:** Processes noun phrases (e.g., "striped cat") to generate embeddings that guide the mask decoder.9  
* **Fusion Encoder:** This component is critical for "exemplar-based" prompting. When a user crops a section of an image to say "find objects like this," the fusion encoder conditions the image features on this visual prompt.9  
* **Presence Head:** A novel component in SAM 3 that predicts a binary "presence token"—a global token indicating whether the target concept exists in the image at all.4 SAM 3 Labeller will utilize this token to suppress false positives before they reach the canvas, a feature unavailable in SAM 2\.

#### **2.1.2 Video Architecture and Linear Scaling**

In video contexts, SAM 3 tracks objects using "masklets"—spatiotemporal masks that span multiple frames. A critical architectural constraint identified in the research is that SAM 3’s inference cost scales linearly with the number of objects being tracked, as each object is processed separately using shared per-frame embeddings.5 This differs from architectures that might process the whole scene at once. Consequently, SAM 3 Labeller must implement **Batch Object Processing**: the UI cannot promise real-time tracking for 100 concurrent objects on a single GPU. Instead, the backend must serialize tracking requests or parallelize them across multiple GPUs (e.g., up to 64 objects on 8 H200s).7

### **2.2 Hybrid Inference Strategy**

To balance the massive VRAM requirements of the 848M parameter model with the need for interactive UI responsiveness, SAM 3 Labeller employs a tiered inference strategy.

#### **2.2.1 Tier 1: The Heavy Lift (Server-Side)**

* **Infrastructure:** The primary inference engine runs on NVIDIA H200 GPUs. Research indicates the H200 can process a single image with 100+ detected objects in approximately 30ms.9  
* **Workload:** This tier handles the initial "Promptable Concept Segmentation" (PCS). When a user types "detect cars," the H200 cluster processes the request, generates the masklets, and returns the heavy vector data.  
* **Video Processing:** All long-horizon video tracking and memory bank updates occur here due to the high memory consumption of maintaining temporal context for multiple objects.12

#### **2.2.2 Tier 2: The Interactive Edge (Client-Side)**

* **Infrastructure:** The browser client utilizes ONNX Runtime Web with a WebGPU backend.11  
* **Model:** A distilled "Tiny" variant of the model (e.g., EdgeSAM or MobileSAM) is loaded directly into the user's browser.14  
* **Workload:** This tier handles "hover interactions" and "smart polygon" adjustments. When a user wants to correct a small error in a mask, the round-trip latency to the cloud is unacceptable. The local WebGPU model processes these geometric refinements in real-time (\>30 FPS on standard hardware) 15, syncing the final result back to the server only upon completion.

### **2.3 Data Engine Compatibility**

SAM 3 Labeller is designed to be compatible with the data engine methodologies used to train SAM 3 itself. The model was trained on the SA-Co (Segment Anything with Concepts) dataset, which contains over 4 million unique concepts.5 The platform’s internal data structure mimics the SA-Co format, storing data as (Image, Noun Phrase, Mask) triplets rather than the traditional (Image, Class ID, BBox) format. This ensures that data exported from SAM 3 Labeller is immediately ready for fine-tuning SAM 3 variants without complex conversion logic.10

### **2.4 Deployment Topology**

The system requires a containerized deployment (Docker) to manage the dependencies of the PyTorch-based inference servers.16

* **Inference Nodes:** Scalable clusters of GPU nodes (H100/H200).  
* **API Gateway:** Handles request routing, specifically directing "heavy" video requests to high-VRAM instances and "light" image requests to lower-tier instances (e.g., A10G) to optimize cost.17  
* **State Management:** Redis is used to cache the "memory embeddings" of SAM 3 for active video sessions, preventing the need to re-encode the video for every new interaction.

---

## **3\. Functional Specifications**

### **3.1 Feature Set A: Promptable Concept Segmentation (PCS)**

This feature set represents the primary workflow of SAM 3 Labeller, replacing the manual toolbar of legacy tools.

#### **3.1.1 Natural Language Concept Input**

* **Requirement:** The interface must provide a global "Concept Command Bar" distinct from a standard search bar.  
* **Mechanism:** Users input short noun phrases (e.g., "player in red"). The system passes this text to the Meta Perception Encoder.5  
* **Presence Verification:** The system must display the "Presence Score" derived from the SAM 3 Presence Head.9 If the score is below a configurable threshold (default 0.7), the UI visually distinguishes the results as "Low Confidence" (e.g., using a dashed outline or yellow tint) to solicit human review.  
* **Open Vocabulary Support:** Unlike CVAT or Label Studio which enforce a pre-defined list, this input accepts any text. The system essentially performs zero-shot detection.1

#### **3.1.2 Exemplar-Based Prompting**

* **Requirement:** Users must be able to define a concept visually without text.  
* **Workflow:** The user selects a "Crop Tool," draws a box around a unique object (e.g., a specific type of bolt on a machine), and marks it as a "Positive Exemplar."  
* **Mechanism:** The SAM 3 Fusion Encoder ingests this image crop and performs a visual search across the dataset/video for similar instances.4  
* **Multi-Exemplar Refinement:** The user can provide multiple crops—both positive and negative. For example, cropping a "bolt" (positive) and a "rivet" (negative) to force the model to discriminate between visually similar items. This utilizes SAM 3’s ability to accept combined text and image exemplars for precise control.9

#### **3.1.3 Batch Auto-Labeling**

* **Requirement:** Application of a validated prompt across a dataset.  
* **Performance Constraint:** The system must throttle batch requests based on available GPU resources. Processing 100+ objects per image takes \~30ms on an H200, but the "Presence Token" check allows the system to skip empty images entirely, significantly speeding up the pipeline.4

### **3.2 Feature Set B: Spatiotemporal Video Annotation**

Video annotation is treated as a distinct modality due to the "masklet" architecture.

#### **3.2.1 Masklet Visualization and Interaction**

* **Requirement:** The timeline must visualize objects not as discrete keyframes but as continuous "Masklet Bars."  
* **Interaction:** Clicking a masklet bar selects that object ID across the entire video duration.  
* **Tracking Logic:** The system uses SAM 3’s tracker (inherited and improved from SAM 2\) to predict the masklet’s trajectory.5  
* **Constraint:** Since inter-object communication is absent in SAM 3’s tracking 5, the UI must allow the user to manually resolve collisions where two masklets overlap and the model fails to discern depth (occlusion).

#### **3.2.2 Bi-Directional Correction Propagation**

* **Requirement:** When a user corrects a mask on frame $T$, the system must propagate this correction to frames $T-n$ and $T+n$.  
* **Mechanism:** The correction updates the memory bank embeddings. The system triggers a re-inference of the surrounding frames using the updated memory context.8  
* **Feedback Loop:** The UI must indicate "Processing Propagation" to the user, as this operation is computationally expensive and not instantaneous on the client side.

#### **3.2.3 ID Management and Switching**

* **Problem:** Automated trackers frequently suffer from ID switching (e.g., ID 1 becomes ID 2 after passing behind a tree).18  
* **Requirement:** The UI must provide a "Merge Tracks" and "Split Track" tool.  
  * *Merge:* User selects ID 1 (frames 0-50) and ID 2 (frames 55-100) and combines them into a single semantic entity.  
  * *Split:* User identifies that ID 1 actually jumps to a different object at frame 40, and splits the track into two distinct IDs.  
* **Data Consistency:** These operations must update the underlying JSON track attributes to ensure COCO-Video or MOT compliance.19

### **3.3 Feature Set C: Collaborative Data Management**

To support enterprise workflows, SAM 3 Labeller includes features for team coordination and data integrity.

#### **3.3.1 Real-Time Consensus Voting**

* **Requirement:** For high-stakes datasets, multiple annotators must label the same image to ensure ground truth accuracy.  
* **Mechanism:** The system assigns the same task to 3 users. It calculates the Intersection over Union (IoU) of their masks in real-time.  
* **Thresholding:** If the IoU is \>0.85, the masks are automatically merged (consensus). If \<0.85, the task is flagged for a "Super Reviewer".20  
* **Reduction of Bias:** This consensus mechanism is critical for validating the "open vocabulary" prompts, ensuring that "red car" implies the same visual concept to all annotators.

#### **3.3.2 Role-Based Access Control (RBAC)**

* **Roles:**  
  * *Admin:* Full access to ontology, billing, and model deployment.  
  * *Reviewer:* Can approve/reject annotations and view annotator analytics.  
  * *Labeler:* Restricted to the "Verify" and "Refine" interfaces; cannot alter project settings.  
* **Implementation:** This mirrors the RBAC structure of Roboflow Enterprise 22, enabling secure collaboration for large teams.

#### **3.3.3 Dynamic Ontology Mapping**

* **Requirement:** While input prompts are open-ended (text), export formats often require fixed class IDs (e.g., YOLO requires integer class IDs).  
* **Mechanism:** An "Ontology Mapper" interface allows admins to group various text prompts (e.g., "cat", "kitten", "feline") under a single export class label ("cat"). This bridges the gap between PCS and traditional supervised learning pipelines.23

---

## **4\. Infrastructure & Performance Strategy**

### **4.1 GPU Resource Planning and Cost Analysis**

The economic viability of SAM 3 Labeller hinges on efficient GPU utilization. Hosting the full 848M parameter SAM 3 model on H100s is costly.

The following table outlines the projected cost structure based on current cloud rental rates 17:

| Hardware | Approx. Cost/Hour | Use Case in SAM 3 Labeller | Performance Metrics |
| :---- | :---- | :---- | :---- |
| **NVIDIA H100 (PCIe)** | $2.00 \- $4.50 | Heavy Batch Inference (Video / Initial Segment) | \~30ms/image (100 objs) 9 |
| **NVIDIA A100 (80GB)** | $1.20 \- $2.50 | Standard Inference / Dev Environment | \~50-60ms/image |
| **NVIDIA A10G** | $0.60 \- $1.00 | Lightweight / Single Image Inference | Slower, lower batch size |
| **Consumer GPU / WebGPU** | Free (Client) | Interactive Refinement (EdgeSAM) | Real-time interaction |

**Optimization Insight:** To maintain margins, SAM 3 Labeller will default to A100s for general usage and dynamically spin up H100/H200 instances only for "Video Processing" queues where the linear scaling of masklets demands maximum throughput.5

### **4.2 Client-Side Acceleration (WebGPU)**

Relying solely on server-side inference introduces network latency that breaks the "flow" of annotation.

* **Technology:** The client uses ONNX Runtime Web.13  
* **Model Distillation:** The platform delivers a quantized version of EdgeSAM or MobileSAM to the browser. These models are distilled from the heavy ViT-based SAM image encoder into pure CNN-based architectures.14  
* **Performance:** This enables the "Magic Wand" tool to update masks at \>30 FPS on an iPhone 14 or standard laptop GPU, strictly for geometric refinement, while the semantic understanding remains server-side.14

### **4.3 Latency Budgeting**

* **Initial Concept Search:** \< 2 seconds (Server-side H100).  
* **Video Tracking (1 min clip):** \< 30 seconds (Batch processing on H100s).  
* **Interactive Refinement:** \< 16ms (60 FPS) via WebGPU.  
* **Mask Propagation:** \< 500ms per keyframe update.

---

## **5\. User Experience (UX) and Interface Design**

### **5.1 The "Verifier" Persona**

The UX is designed for a "Verifier" persona rather than a "Creator." The system assumes the AI is 80-90% correct (based on SAM 3 achieving 88% of human performance on benchmarks 9). The UI focuses on high-speed rejection or approval of proposals.

### **5.2 The Workspace Layout**

The interface follows a standard three-pane layout optimized for dense information display.

#### **5.2.1 Left Pane: The Concept Ledger**

* **Function:** Replaces the traditional "Class List."  
* **Components:**  
  * **Active Prompts:** A list of the text queries currently active on the image (e.g., "Safety Vest").  
  * **Instance Counts:** "14 Instances Found" next to the prompt.  
  * **Confidence Indicators:** A color-coded bar indicating the "Presence Token" confidence. Green \= High, Yellow \= Mixed, Red \= Low.

#### **5.2.2 Center Pane: The Semantic Canvas**

* **Technology:** Rendered using Three.js or Konva.js to support thousands of vector masklets without DOM heaviness.  
* **Interaction Model:**  
  * *Hover:* Highlights the mask and displays the associated text prompt.  
  * *Click:* Selects the instance for attribute editing.  
  * *Right-Click:* Opens the "Negative Exemplar" context menu to suppress the mask.  
* **Visual Prompting Overlay:** When the user engages the "Exemplar Tool," the canvas dims, and the user draws a box. The system immediately highlights visually similar objects in real-time.27

#### **5.2.3 Bottom Pane: The Masklet Timeline**

* **Function:** Visualizes the temporal dimension of the data.  
* **Design Pattern:**  
  * **Ribbons:** Each object is a horizontal ribbon.  
  * **Confidence Gradients:** The ribbon color fades or changes (e.g., Green to Yellow) in frames where the tracker’s confidence drops, guiding the user to audit those specific frames.28  
  * **Keyframe Indicators:** Diamonds indicate frames where a human manually adjusted the mask; lines indicate interpolated/tracked frames.29

### **5.3 Handling Edge Cases and Ambiguity**

* **The "Ambiguity Resolver":** When SAM 3 returns multiple overlapping masks for a single point (a known feature of the SAM architecture to handle ambiguity), the UI presents a "1-of-3" selector tooltip, allowing the user to pick the correct depth layer (e.g., the person vs. the shirt vs. the button).4

---

## **6\. Data Management and Export**

### **6.1 Export Compatibility**

SAM 3 Labeller must support the ecosystem of formats required by downstream ML operations (MLOps).

* **SA-Co Format:** The native JSON format of the platform, mirroring the dataset used to train SAM 3\. This supports nested concept descriptions 30 and is essential for users who wish to fine-tune SAM 3 on their own data.10  
* **COCO & COCO-Video:** The standard for object detection and segmentation. The system must map the "Masklet IDs" to COCO "Track IDs" to support video instance segmentation benchmarks.19  
* **YOLOv8/v11 Format:** Text-based format for detection. Requires the "Ontology Mapper" to flatten the open-vocabulary text prompts into integer class IDs.31  
* **MOT Challenge:** A CSV-based format specifically for multi-object tracking, requiring precise frame-by-frame bounding box coordinates and stable IDs.32

### **6.2 Quality Assurance Workflows**

* **Review Queue:** A dedicated interface for "Reviewers" that presents only the items flagged by the Consensus Voting system.  
* **Automated QA:** The system uses the SAM 3 Presence Token to flag "Ghost Annotations" (masks that exist where the model predicts the concept is absent) and "Missed Detections" (where the model predicts presence, but no mask exists).4

---

## **7\. Implementation Roadmap**

### **7.1 Phase 1: Core PCS Engine (Months 1-3)**

* **Objective:** Deliver image-only annotation with Text-to-Mask capabilities.  
* **Milestones:**  
  * Deploy SAM 3 inference API on H100s.5  
  * Implement the "Concept Command Bar" and Perception Encoder integration.  
  * Achieve COCO export parity.  
  * Integrate WebGPU EdgeSAM for client-side responsiveness.

### **7.2 Phase 2: Video & Tracking (Months 4-6)**

* **Objective:** Unlock spatiotemporal annotation.  
* **Milestones:**  
  * Implement "Masklet" visualization in the timeline.  
  * Deploy the SAM 3 Tracker with memory bank support on the backend.  
  * Build "Merge/Split Track" UI tools for ID management.  
  * Optimize H200 batch processing for video uploads.

### **7.3 Phase 3: Ecosystem & Collaboration (Months 7-9)**

* **Objective:** Enterprise readiness.  
* **Milestones:**  
  * Implement Consensus Voting and RBAC.  
  * Launch the "Fine-Tune SAM 3" workflow, allowing users to train adapter layers on their verified data.33  
  * Add support for SAM 3D reconstruction exports.34

---

## **8\. Pricing and Business Strategy**

### **8.1 Cost-Driven Pricing Model**

Unlike legacy tools that charge per user seat, SAM 3 Labeller’s costs are compute-dominated. The pricing model must reflect the H100/H200 usage.

* **Metric:** "Masklet-Seconds." Processing 1 minute of video with 5 tracked objects creates 300 Masklet-Seconds of compute load.  
* **Strategy:**  
  * **Freemium:** Uses the "Public" Roboflow Universe model. Users contribute data to the public domain in exchange for free compute (running on cheaper A10s or shared queues).35  
  * **Pro:** Monthly subscription \+ Compute Credits. Access to private H100 queues.  
  * **Enterprise:** Private VPC deployment. Critical for customers with data sovereignty requirements who need the model (SAM 3\) to run entirely within their firewall.16

### **8.2 Strategic Differentiation**

SAM 3 Labeller competes not on price, but on *throughput*. By proving the metric that "Negative Prompts are 5x faster" and "Positive Prompts are 36% faster" 5, the platform positions itself as a productivity multiplier that offsets the higher compute costs.

---

## **9\. Conclusion**

SAM 3 Labeller represents the inevitable evolution of the data annotation stack. The release of SAM 3 has rendered pixel-by-pixel annotation tools obsolete for a vast majority of use cases. By embracing **Promptable Concept Segmentation**, SAM 3 Labeller moves the human value chain up the stack—from "drawing" to "defining." The technical complexity of this platform is high, requiring a delicate orchestration of massive server-side models (SAM 3 on H200s) and nimble client-side approximations (EdgeSAM on WebGPU). However, the resulting efficiency gains—measured in orders of magnitude for complex tasks—provide a defensible moat against legacy incumbents like CVAT and Label Studio. This PRD outlines a clear path to building a platform that is not just a wrapper for a model, but a comprehensive workspace for the era of semantic computer vision.

---

## **10\. Detailed Feature Descriptions and User Flows**

### **10.1 User Flow: The "Cold Start" Annotation**

The most challenging phase in annotation is the "Cold Start"—beginning a project with no pre-existing labels. SAM 3 Labeller optimizes this via the PCS (Promptable Concept Segmentation) workflow.

#### **10.1.1 Step 1: Data Ingestion & Pre-Processing**

* **User Action:** User uploads a raw video file (e.g., 4K MP4 drone footage).  
* **System Process:**  
  * The video is transcoded into a stream-friendly format (HLS/DASH).  
  * **Keyframe Extraction:** The system automatically extracts keyframes based on scene change detection, not just fixed time intervals, to optimize the tracking context for SAM 3\.36  
  * **Embedding Generation:** The system pre-computes image embeddings using the Meta Perception Encoder. This is a one-time heavy compute cost that enables real-time prompting later.

#### **10.1.2 Step 2: Concept Definition (The "Magic Wand")**

* **User Action:** User types "Solar Panel" into the Command Bar.  
* **System Process:**  
  * The text prompt is tokenized and passed to the SAM 3 detector.  
  * The "Presence Head" evaluates the frames.  
  * **Result:** The system returns 500 potential instances across the video timeline.  
* **UI Feedback:** The timeline lights up with "proposed" masklets in a distinct color (e.g., Cyan). The confidence score is displayed.

#### **10.1.3 Step 3: The Verification Loop**

* **User Action:** The user scrubs through the timeline. They notice a skylight incorrectly identified as a solar panel.  
* **User Interaction:** The user performs a "Negative Click" (Right-click) on the skylight in one frame.  
* **System Process (Correction Propagation):**  
  * The system treats this click as a negative geometric prompt.  
  * It updates the memory bank for that specific object ID.  
  * SAM 3 re-propagates the track forward and backward. The skylight mask disappears from the entire sequence.8  
* **Efficiency Gain:** A single click resolves the error across hundreds of frames, demonstrating the power of the masklet architecture over frame-by-frame editing.

### **10.2 Feature Deep Dive: The "Memory Bank" Visualization**

One of the most opaque aspects of SAM 2 and 3 is the "Memory Bank"—the internal state that tracks objects. SAM 3 Labeller exposes this to power users to debug tracking failures.

* **Feature:** "Memory Context Indicators."  
* **Description:** In the timeline, specific frames are marked with a "Brain Icon." These represent frames that are currently stored in the model's limited memory bank (FIFO buffer).  
* **Utility:** If tracking drifts, the user can see that the model has "forgotten" the initial frame where the object appeared clearly. The user can force-mark a frame as a "Memory Keyframe," pinning it in the model's context window to ensure long-term stability.8

### **10.3 Feature Deep Dive: Auto-Distillation for Offline Mode**

For field teams (e.g., agricultural researchers) who annotate without internet, SAM 3 Labeller offers a unique "Sync to Edge" feature.

* **Workflow:**  
  * User selects a dataset while online.  
  * SAM 3 Labeller runs a "Distillation Job" on the server, creating a lightweight .onnx model specific to the concepts in that project (e.g., fine-tuned for "Crop Disease").33  
  * This model is cached in the browser via the File System Access API.  
* **Result:** The user can annotate offline using the WebGPU engine, and the data syncs back to the cloud when connectivity is restored. This bridges the gap between the massive SAM 3 server model and practical field usage.14

---

## **11\. System Reliability and Error Handling**

### **11.1 Handling "Hallucinations" and False Positives**

Foundational models can "hallucinate" masks on noise.

* **Mitigation:** SAM 3 Labeller implements a "Minimum Area Threshold" and "Stability Score" filter. Masks that are too small or jitter significantly between frames (low temporal consistency) are automatically flagged for review or discarded.28

### **11.2 Graceful Degradation**

If the H100 cluster is at capacity or the user's credit balance is low:

* **Fallback:** The system automatically degrades from SAM 3 (Server) to EdgeSAM (Client).  
* **UI Notification:** A "Low Power Mode" icon appears. The "Text Prompt" feature becomes unavailable (as EdgeSAM is visual-only or limited text), and the user is restricted to box/point prompting until resources are available.

### **11.3 Data Integrity and Versioning**

* **Versioning:** Every annotation session creates a "Dataset Version" (snapshot). This allows users to roll back to "Pre-SAM Auto-Label" states if the model performs poorly.  
* **Format Safety:** The internal storage format strictly separates "Model Predictions" from "Human Annotations." Model predictions are ephemeral until verified; Human annotations are immutable without explicit overwrite. This prevents the AI from overwriting valid human work during batch updates.37

---

## **12\. Future-Proofing: 3D and Multimodal Agents**

### **12.1 SAM 3D Integration**

Meta’s release includes SAM 3D for point cloud and 3D reconstruction.34

* **Roadmap Item:** "SAM 3 Labeller 3D."  
* **Feature:** A 3D viewport (using Three.js) where masks generated in 2D images are projected onto 3D point clouds (if available).  
* **Use Case:** Robotics and Digital Twin creation. The user annotates a "Chair" in a 2D photo, and SAM 3D propagates that label to the 3D mesh of the room.

### **12.2 Integration with MLLMs (SAM 3 Agent)**

Research indicates SAM 3 can act as a tool for Multimodal Large Language Models (MLLMs).4

* **Future Feature:** "Conversational Annotation."  
* **Workflow:** User asks a chat interface: "Find all the people who are *not* wearing safety gear."  
* **Mechanism:** The MLLM parses the logic ("not wearing safety gear"), identifies the target concepts, and instructs SAM 3 to segment "people" and "safety gear," then performs the geometric subtraction logic to highlight the violations. This moves SAM 3 Labeller towards a "Reasoning Engine" rather than just a labeling tool.

---

## **13\. Comparative Feature Matrix: SAM 3 Labeller vs. Incumbents**

The following table summarizes the specific technical advantages of SAM 3 Labeller over the primary competitors identified in the research.

| Feature | SAM 3 Labeller (SAM 3 Native) | Roboflow | CVAT | X-AnyLabeling |
| :---- | :---- | :---- | :---- | :---- |
| **Concept Segmentation** | **Native PCS (Text-to-Mask)** | Wrapper (API Call) | No Native Support | Plugin (Basic) |
| **Video Tracking** | **Masklet & Memory Bank** | Frame-by-Frame / Interpolation | Kalman Filter / Interpolation | Tracking-by-Detection |
| **Inference Engine** | **Hybrid (H200 \+ WebGPU)** | Server-Side API | Client-Side / Serverless | Local Execution |
| **Correction Propagation** | **Bi-Directional (Memory)** | No | No | No |
| **Ontology** | **Open Vocabulary (Dynamic)** | Fixed Classes | Fixed Schema | Import Required |
| **Offline Capability** | **Yes (Distilled EdgeSAM)** | Limited | Yes (Local Install) | Yes (Desktop App) |
| **Collaboration** | **Real-Time Consensus** | Async Assignment | Job-Based | File-Based |

**Summary of Advantage:** While Roboflow offers a polished UX and CVAT offers robust video tools, neither platform was architected for the *semantic* nature of SAM 3\. They treat the model as a black box plugin. SAM 3 Labeller’s advantage lies in exposing the internals of SAM 3—the presence token, the memory bank, and the masklet—directly in the UI, allowing for a workflow that is fundamentally faster and more accurate for the next generation of computer vision tasks.

#### **Works cited**

1. What is Segment Anything 3 (SAM 3)? Segment Anything with Concepts \- Roboflow Blog, accessed November 21, 2025, [https://blog.roboflow.com/what-is-sam3/](https://blog.roboflow.com/what-is-sam3/)  
2. New Segment Anything Models Make it Easier to Detect Objects and Create 3D Reconstructions \- About Meta, accessed November 21, 2025, [https://about.fb.com/news/2025/11/new-sam-models-detect-objects-create-3d-reconstructions/](https://about.fb.com/news/2025/11/new-sam-models-detect-objects-create-3d-reconstructions/)  
3. \[R\] SAM 3 is now here\! Is segmentation already a done deal? : r/MachineLearning \- Reddit, accessed November 21, 2025, [https://www.reddit.com/r/MachineLearning/comments/1p1y74p/r\_sam\_3\_is\_now\_here\_is\_segmentation\_already\_a/](https://www.reddit.com/r/MachineLearning/comments/1p1y74p/r_sam_3_is_now_here_is_segmentation_already_a/)  
4. Meta AI Releases Segment Anything Model 3 (SAM 3\) for Promptable Concept Segmentation in Images and Videos \- MarkTechPost, accessed November 21, 2025, [https://www.marktechpost.com/2025/11/20/meta-ai-releases-segment-anything-model-3-sam-3-for-promptable-concept-segmentation-in-images-and-videos/](https://www.marktechpost.com/2025/11/20/meta-ai-releases-segment-anything-model-3-sam-3-for-promptable-concept-segmentation-in-images-and-videos/)  
5. Introducing Meta Segment Anything Model 3 and Segment Anything Playground \- AI at Meta, accessed November 21, 2025, [https://ai.meta.com/blog/segment-anything-model-3/](https://ai.meta.com/blog/segment-anything-model-3/)  
6. facebook/sam3 \- Hugging Face, accessed November 21, 2025, [https://huggingface.co/facebook/sam3](https://huggingface.co/facebook/sam3)  
7. SAM 3: SEGMENT ANYTHING WITH CONCEPTS \- OpenReview, accessed November 21, 2025, [https://openreview.net/pdf/9cb68221311aa4d88167b66c0c84ef569e37122f.pdf](https://openreview.net/pdf/9cb68221311aa4d88167b66c0c84ef569e37122f.pdf)  
8. Introducing Meta Segment Anything Model 2 (SAM 2), accessed November 21, 2025, [https://ai.meta.com/sam2/](https://ai.meta.com/sam2/)  
9. SAM 3: Segment Anything with Concepts \- Ultralytics YOLO Docs, accessed November 21, 2025, [https://docs.ultralytics.com/models/sam-3/](https://docs.ultralytics.com/models/sam-3/)  
10. Launch: Use Segment Anything 3 (SAM 3\) with Roboflow, accessed November 21, 2025, [https://blog.roboflow.com/sam3/](https://blog.roboflow.com/sam3/)  
11. Using WebGPU | onnxruntime, accessed November 21, 2025, [https://onnxruntime.ai/docs/tutorials/web/ep-webgpu.html](https://onnxruntime.ai/docs/tutorials/web/ep-webgpu.html)  
12. VRAM requirements? · Issue \#6 · facebookresearch/sam-3d-objects \- GitHub, accessed November 21, 2025, [https://github.com/facebookresearch/sam-3d-objects/issues/6](https://github.com/facebookresearch/sam-3d-objects/issues/6)  
13. SAM2 running in the browser with onnxruntime-web : r/computervision \- Reddit, accessed November 21, 2025, [https://www.reddit.com/r/computervision/comments/1gq9so2/sam2\_running\_in\_the\_browser\_with\_onnxruntimeweb/](https://www.reddit.com/r/computervision/comments/1gq9so2/sam2_running_in_the_browser_with_onnxruntimeweb/)  
14. EdgeSAM | MMLab@NTU, accessed November 21, 2025, [https://www.mmlab-ntu.com/project/edgesam/](https://www.mmlab-ntu.com/project/edgesam/)  
15. EdgeSAM: Prompt-In-the-Loop Distillation for SAM \- arXiv, accessed November 21, 2025, [https://arxiv.org/pdf/2312.06660](https://arxiv.org/pdf/2312.06660)  
16. Roboflow Features, accessed November 21, 2025, [https://roboflow.com/features](https://roboflow.com/features)  
17. Pricing \- Hugging Face, accessed November 21, 2025, [https://huggingface.co/pricing](https://huggingface.co/pricing)  
18. Video Annotation Made Simple: Best Tools & Techniques \- Roboflow Blog, accessed November 21, 2025, [https://blog.roboflow.com/video-annotation/](https://blog.roboflow.com/video-annotation/)  
19. COCO Format Export \- Encord Docs, accessed November 21, 2025, [https://docs.encord.com/platform-documentation/Annotate/annotate-export/annotate-export-coco](https://docs.encord.com/platform-documentation/Annotate/annotate-export/annotate-export-coco)  
20. Is Your Training Data Trustworthy? How to Use Precision & Recall for Annotation QA \- CVAT, accessed November 21, 2025, [https://www.cvat.ai/resources/blog/precision-recall-accuracy-annotation-quality-metrics](https://www.cvat.ai/resources/blog/precision-recall-accuracy-annotation-quality-metrics)  
21. Consensus-based annotation \- CVAT Documentation, accessed November 21, 2025, [https://docs.cvat.ai/docs/qa-analytics/consensus/](https://docs.cvat.ai/docs/qa-analytics/consensus/)  
22. Role-Based Access Control (RBAC) | Roboflow Docs, accessed November 21, 2025, [https://docs.roboflow.com/team-members/role-based-access-control](https://docs.roboflow.com/team-members/role-based-access-control)  
23. Taxonomies and metadata: 5 key tips for UX writers, accessed November 21, 2025, [https://uxcontent.com/taxonomies-and-metadata-5-key-tips-for-ux-writers/](https://uxcontent.com/taxonomies-and-metadata-5-key-tips-for-ux-writers/)  
24. NVIDIA GPUs H100 vs. A100 \- Architecture, Performance, and Cost Comparison, accessed November 21, 2025, [https://www.trgdatacenters.com/resource/h100-vs-a100/](https://www.trgdatacenters.com/resource/h100-vs-a100/)  
25. Pricing | Runpod GPU cloud computing rates, accessed November 21, 2025, [https://www.runpod.io/pricing](https://www.runpod.io/pricing)  
26. \[2312.06660\] EdgeSAM: Prompt-In-the-Loop Distillation for SAM \- arXiv, accessed November 21, 2025, [https://arxiv.org/abs/2312.06660](https://arxiv.org/abs/2312.06660)  
27. Segment Anything Playground \- Meta AI Demos, accessed November 21, 2025, [https://www.aidemos.meta.com/segment-anything](https://www.aidemos.meta.com/segment-anything)  
28. Prompt Self-Correction for SAM2 Zero-Shot Video Object Segmentation \- MDPI, accessed November 21, 2025, [https://www.mdpi.com/2079-9292/14/18/3602](https://www.mdpi.com/2079-9292/14/18/3602)  
29. BeaverDam: Video Annotation Tool for Computer Vision Training Labels \- University of California, Berkeley, accessed November 21, 2025, [https://digicoll.lib.berkeley.edu/record/139880/files/EECS-2016-193.pdf](https://digicoll.lib.berkeley.edu/record/139880/files/EECS-2016-193.pdf)  
30. DeepJSONEval: Benchmarking Complex Nested JSON Data Mining for Large Language Models \- arXiv, accessed November 21, 2025, [https://arxiv.org/html/2509.25922v1](https://arxiv.org/html/2509.25922v1)  
31. Developing Real-Time Object Detection Using YOLOv8 and Custom Datasets \- Medium, accessed November 21, 2025, [https://medium.com/@lfoster49203/developing-real-time-object-detection-using-yolov8-and-custom-datasets-db01ea580c9c](https://medium.com/@lfoster49203/developing-real-time-object-detection-using-yolov8-and-custom-datasets-db01ea580c9c)  
32. Instructions \- MOT Challenge, accessed November 21, 2025, [https://motchallenge.net/instructions/](https://motchallenge.net/instructions/)  
33. How to Fine-Tune Segment Anything 3 (SAM 3\) on a Custom Dataset \- Roboflow Blog, accessed November 21, 2025, [https://blog.roboflow.com/fine-tune-sam3/](https://blog.roboflow.com/fine-tune-sam3/)  
34. Introducing SAM 3D: Powerful 3D Reconstruction for Physical World Images, accessed November 21, 2025, [https://ai.meta.com/blog/sam-3d/](https://ai.meta.com/blog/sam-3d/)  
35. Plans | Roboflow Docs, accessed November 21, 2025, [https://docs.roboflow.com/billing/plans](https://docs.roboflow.com/billing/plans)  
36. Video Annotation with Object Tracking Techniques \- V2Solutions, accessed November 21, 2025, [https://www.v2solutions.com/blogs/optimizing-video-annotation-with-advanced-object-tracking-techniques/](https://www.v2solutions.com/blogs/optimizing-video-annotation-with-advanced-object-tracking-techniques/)  
37. Collaborate on Labeling \- Roboflow Docs, accessed November 21, 2025, [https://docs.roboflow.com/annotate/team-collaboration](https://docs.roboflow.com/annotate/team-collaboration)