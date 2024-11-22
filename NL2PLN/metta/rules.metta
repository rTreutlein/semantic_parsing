

!(add-atom &kb
           (: MkΣ
              (-> (: $p (-> (: $_ $a) Type)) ; Premise 1.  We
                                             ;   need to use (: $_ $a)
                                             ;   as opposed to just $a
                                             ;   to be fully consistent with
                                             ;   The (: PROOF PREMISE)
                                             ;   notation, till it becomes
                                             ;   optional.
                  (-> (: $x $a)              ; Premise 2
                      (-> (: $prf ($p $x))   ; Premise 3
                          (Σ (: $x $a) ($p $x))))))); Conclusion(

!(add-atom &kb (: fst (-> (: $prf (Σ (: $elem $type) $body)) $type)))
!(add-atom &kb (: snd (-> (: $prf (Σ (: (fst $prf) $_) $body)) $body)))

!(add-atom &kb (: MkProduct (-> (: $a $at) (-> (: $b $bt) (* $at $bt)))))

!(add-atom &kb (: fst (-> (* $a $b) $a)))
!(add-atom &kb (: snd (-> (* $a $b) $b)))

!(add-atom &kb (: MkSum (-> (: $a $at) (+ $at $var))))
!(add-atom &kb (: MkSum (-> (: $a $at) (+ $var $at))))
