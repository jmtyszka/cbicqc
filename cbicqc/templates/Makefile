# Key files
T1_head = MNI152_T1_2mm.nii.gz
T1_brain = MNI152_T1_2mm_brain.nii.gz
brain_mask = MNI152_T1_2mm_brain_mask.nii.gz
brain_mask_fill = MNI152_T1_2mm_brain_mask_fill.nii.gz
head_mask = MNI152_T1_2mm_head_mask.nii.gz
head_mask_fill = MNI152_T1_2mm_head_mask_fill.nii.gz

all: $(head_mask_fill) $(brain_mask_fill)

$(head_mask_fill): $(head_mask)
	fslmaths $(head_mask) -s 5.0 -thr 0.5 -bin -fillh $(head_mask_fill)

$(head_mask):  $(T1_head)
	fslmaths $(T1_head) -thr 1000 -bin $(head_mask)

$(brain_mask_fill): $(brain_mask)
	fslmaths $(brain_mask) -fillh $(brain_mask_fill)

clean:
	rm -rf $(brain_mask_fill) $(head_mask) $(head_mask_fill)
