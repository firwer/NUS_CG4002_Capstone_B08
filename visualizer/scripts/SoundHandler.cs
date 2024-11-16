using UnityEngine;

/// <summary>
/// Play sound effects for the player actions
/// </summary>
public class SoundHandler : MonoBehaviour
{
    public AudioClip gunAudio;
    public AudioClip ballAudio;
    public AudioClip bowlingBallAudio;
    public AudioClip rainBombThrowAudio;
    public AudioClip onHitAudio;
    public AudioClip onHitRainBombAudio;
    public AudioClip takeDamageAudio;
    public AudioClip equipShieldAudio;
    public AudioClip reviveAudio;
    public AudioClip diedAudio;
    public AudioClip reloadAudio;
    public AudioClip halleluiahAudio;

    public Transform player;
    public void PlayGunAudio()
    {
        AudioSource.PlayClipAtPoint(gunAudio, player.position);
    }

    public void PlayThrowBallAudio()
    {
        AudioSource.PlayClipAtPoint(ballAudio, player.position);
    }
    public void PlayThrowBowlingBallAudio()
    {
        AudioSource.PlayClipAtPoint(bowlingBallAudio, player.position);
    }

    public void PlayThrowRainBombAudio()
    {
        AudioSource.PlayClipAtPoint(rainBombThrowAudio, player.position);
    }
    public void PlayOnHitAudio()
    {
        AudioSource.PlayClipAtPoint(onHitAudio, player.position);
    }
    public void PlayOnHitRainBombAudio()
    {
        AudioSource.PlayClipAtPoint(onHitRainBombAudio, player.position);
    }
    public void PlayTakeDamageAudio()
    {
        AudioSource.PlayClipAtPoint(takeDamageAudio, player.position);
    }
    public void PlayEquipShieldAudio()
    {
        AudioSource.PlayClipAtPoint(equipShieldAudio, player.position);
    }
    public void PlayReviveAudio()
    {
        AudioSource.PlayClipAtPoint(reviveAudio, player.position);
    }
    public void PlayDiedAudio()
    {
        //AudioSource.PlayClipAtPoint(diedAudio, player.position);
        AudioSource.PlayClipAtPoint(halleluiahAudio, player.position);
    }
    public void PlayReloadAudio()
    {
        AudioSource.PlayClipAtPoint(reloadAudio, player.position);
    }
    public void PlayLogOutAudio()
    {
        AudioSource.PlayClipAtPoint(halleluiahAudio, player.position);
    }
}
