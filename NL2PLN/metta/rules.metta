
;!(add-atom &kb
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

;!(add-atom &kb (: fst (-> (: $prf (Σ (: $elem $type) $body)) $type)))
;!(add-atom &kb (: snd (-> (: $prf (Σ (: (fst $prf) $_) $body)) $body)))

;!(add-atom &kb (: MkProduct (-> (: $a $at) (-> (: $b $bt) (* $at $bt)))))

;!(add-atom &kb (: fst (-> (: $prf (* $a $b)) $a)))
;!(add-atom &kb (: snd (-> (: $prf (* $a $b)) $b)))

;!(add-atom &kb (: MkSumLeft (-> (: $a $at) (| $at $bt))))
;!(add-atom &kb (: MkSumRight (-> (: $b $bt) (| $at $bt))))

!(add-atom &kb (: deduction (-> (: $ab (-> (: $x $a) $b)) 
                            (-> (: $bc (-> (: $x $b) $c)) 
                                (-> (: $x $a) $c)))))

!(add-atom &kb (: contraposition (-> (: $ab (-> (: $a $A) $B))
                                            (-> (: $nb (Not $B)) (Not $A)))))

!(add-atom &kb (: anotate_time (-> (: $ab (-> (: $a $A) $B)) (-> (: $at (TrueAtTime $A $t)) (TrueAtTime $B $t)))))
!(add-atom &kb (: anotate_time (-> (: $ab (-> (: $a $A) $B)) (-> (: $at (TrueAtPlace $A $t)) (TrueAtPlace $B $t)))))
!(add-atom &kb (: anotate_time (-> (: $ab (-> (: $a $A) $B)) (-> (: $at (TrueAtTimePlace $A $t)) (TrueAtTimePlace $B $t)))))
