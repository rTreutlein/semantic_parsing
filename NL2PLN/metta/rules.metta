
;!(add-atom &rules
;           (: MkΣ
;              (-> (: $p (-> (: $_ $a) Type)) ; Premise 1.  We
;                                             ;   need to use (: $_ $a)
;                                             ;   as opposed to just $a
;                                             ;   to be fully consistent with
;                                             ;   The (: PROOF PREMISE)
;                                             ;   notation, till it becomes
;                                             ;   optional.
;                  (-> (: $x $a)              ; Premise 2
;                      (-> (: $prf ($p $x))   ; Premise 3
;                          (Σ (: $x $a) ($p $x))))))); Conclusion(

;!(add-atom &rules (: fst (-> (: $prf (Σ (: $elem $type) $body)) $type)))
;!(add-atom &rules (: snd (-> (: $prf (Σ (: (fst $prf) $_) $body)) $body)))

;!(add-atom &rules (: MkProduct (-> (: $a $at) (-> (: $b $bt) (* $at $bt)))))

;!(add-atom &rules (: fst (-> (: $prf (* $a $b)) $a)))
;!(add-atom &rules (: snd (-> (: $prf (* $a $b)) $b)))

;!(add-atom &rules (: MkSumLeft (-> (: $a $at) (| $at $bt))))
;!(add-atom &rules (: MkSumRight (-> (: $b $bt) (| $at $bt))))

!(add-atom &rules (: deduction (-> (: $ab (-> (: $prfa $a) $b)) 
                            (-> (: $bc (-> (: $prfb $b) $c)) 
                                (-> (: $prfa $a) $c)))))

!(add-atom &rules (: contraposition (-> (: $ab (-> (: $a $A) $B))
                                            (-> (: $nb (Not $B)) (Not $A)))))

!(add-atom &rules (: anotate_time (-> (: $ab (-> (: $a $A) $B)) (-> (: $at (TrueAtTime $A $t)) (TrueAtTime $B $t)))))
!(add-atom &rules (: anotate_time (-> (: $ab (-> (: $a $A) $B)) (-> (: $at (TrueAtPlace $A $t)) (TrueAtPlace $B $t)))))
!(add-atom &rules (: anotate_time (-> (: $ab (-> (: $a $A) $B)) (-> (: $at (TrueAtTimePlace $A $t)) (TrueAtTimePlace $B $t)))))
